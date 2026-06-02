"""Integration tests for iot-mcp-agent components."""

import pytest

from iot_mcp_agent.config import Settings
from iot_mcp_agent.tools.action_tools import ActionTools
from iot_mcp_agent.tools.alarm_tools import AlarmTools
from iot_mcp_agent.tools.device_tools import DeviceTools
from iot_mcp_agent.utils.simulator import DeviceSimulator


class TestSimulatorIntegration:
    """Integration tests using the device simulator."""

    @pytest.fixture
    def simulator(self):
        """Create a simulator instance."""
        return DeviceSimulator()

    @pytest.mark.asyncio
    async def test_device_lifecycle(self, simulator):
        """Test complete device monitoring lifecycle."""
        # 1. List devices
        devices = await simulator.list_devices()
        assert devices["total"] > 0
        device_id = devices["devices"][0]["id"]

        # 2. Get specific device
        device = await simulator.get_device(device_id)
        assert device["id"] == device_id

        # 3. Get measurements
        measurements = await simulator.get_measurements(device_id)
        assert "measurements" in measurements

        # 4. Get alarms
        alarms = await simulator.get_alarms(device_id=device_id)
        assert isinstance(alarms["alarms"], list)

        # 5. Create an alarm
        new_alarm = await simulator.create_alarm(
            device_id=device_id,
            type="c8y_TestAlarm",
            severity="MAJOR",
            text="Integration test alarm",
        )
        assert new_alarm["success"] is True
        assert new_alarm["alarm"]["device_id"] == device_id

    @pytest.mark.asyncio
    async def test_tools_with_simulator(self, simulator):
        """Test all tools working with simulator."""
        device_tools = DeviceTools(simulator)
        alarm_tools = AlarmTools(simulator)
        action_tools = ActionTools(simulator)

        # Get devices
        devices = await device_tools.list_devices(limit=5)
        assert devices["total"] > 0

        # Get first device details
        device_id = devices["devices"][0]["id"]
        device = await device_tools.get_device(device_id)
        assert device["id"] == device_id

        # Get measurements
        measurements = await device_tools.get_measurements(device_id)
        assert "measurements" in measurements

        # Get alarms
        alarms = await alarm_tools.get_alarms(device_id=device_id)
        assert isinstance(alarms["alarms"], list)

        # Create alarm
        new_alarm = await alarm_tools.create_alarm(
            device_id=device_id,
            type="c8y_TemperatureAlarm",
            severity="CRITICAL",
            text="High temperature detected",
        )
        assert new_alarm["success"] is True
        assert new_alarm["alarm"]["severity"] == "CRITICAL"

        # Update config
        config = await action_tools.update_device_config(
            device_id=device_id,
            config_key="reporting_interval",
            config_value="60",
            reason="Integration test",
        )
        assert config["updated"]["reporting_interval"] == "60"

        # Send notification
        notif = await action_tools.send_notification(
            channel="email",
            recipient="test@example.com",
            subject="Test Alert",
            message="This is an integration test notification",
        )
        assert notif["channel"] == "email"

    @pytest.mark.asyncio
    async def test_anomaly_detection_workflow(self, simulator):
        """Test a realistic anomaly detection workflow."""
        device_tools = DeviceTools(simulator)
        alarm_tools = AlarmTools(simulator)

        # List all temperature sensors
        devices = await device_tools.list_devices()

        # Check each device for anomalies
        anomalies = []
        for device in devices["devices"]:
            device_id = device["id"]

            # Get recent measurements
            measurements = await device_tools.get_measurements(
                device_id, limit=10
            )

            # Check for high temperatures (simple anomaly detection)
            for measurement in measurements["measurements"]:
                if "Temperature" in measurement.get("type", ""):
                    value = float(measurement.get("value", 0))
                    if value > 60:  # Critical threshold
                        anomalies.append(
                            {
                                "device_id": device_id,
                                "value": value,
                                "type": measurement["type"],
                            }
                        )

        # Create alarms for anomalies
        for anomaly in anomalies:
            await alarm_tools.create_alarm(
                device_id=anomaly["device_id"],
                type="c8y_TemperatureAlarm",
                severity="CRITICAL",
                text=f"Temperature anomaly: {anomaly['value']}°C",
            )

    @pytest.mark.asyncio
    async def test_device_status_filtering(self, simulator):
        """Test filtering devices by status."""
        device_tools = DeviceTools(simulator)

        # Get available devices
        available = await device_tools.list_devices(status="AVAILABLE")
        if available["devices"]:
            for device in available["devices"]:
                assert device["status"] == "AVAILABLE"

        # Get unavailable devices
        unavailable = await device_tools.list_devices(status="UNAVAILABLE")
        if unavailable["devices"]:
            for device in unavailable["devices"]:
                assert device["status"] == "UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_alarm_severity_filtering(self, simulator):
        """Test filtering alarms by severity."""
        alarm_tools = AlarmTools(simulator)

        # Get critical alarms
        critical = await alarm_tools.get_alarms(severity="CRITICAL")
        for alarm in critical["alarms"]:
            assert alarm["severity"] == "CRITICAL"

        # Get major alarms
        major = await alarm_tools.get_alarms(severity="MAJOR")
        for alarm in major["alarms"]:
            assert alarm["severity"] == "MAJOR"


class TestConfigurationIntegration:
    """Integration tests for configuration loading."""

    def test_settings_with_env_file(self, tmp_path, monkeypatch):
        """Test loading settings from .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_content = """
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-test-123
PLATFORM=simulate
AGENT_MAX_ITERATIONS=25
"""
        env_file.write_text(env_content)

        # Change to temp directory and test
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")

        settings = Settings()
        assert settings.llm_provider == "anthropic"

    def test_default_settings_override(self, monkeypatch):
        """Test default settings can be overridden."""
        monkeypatch.setenv("AGENT_MAX_ITERATIONS", "50")

        settings = Settings()
        assert settings.agent_max_iterations == 50


class TestErrorHandling:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_device_id_handling(self):
        """Test handling of invalid device IDs."""
        simulator = DeviceSimulator()

        # Try to get non-existent device (should handle gracefully)
        result = await simulator.get_device("invalid-device-id-12345")

        # Simulator should return empty or error dict, not raise
        assert isinstance(result, dict)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_measurement_retrieval_no_data(self):
        """Test handling of measurements with no data."""
        simulator = DeviceSimulator()

        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]

            # Request measurements for specific type that may not exist
            result = await simulator.get_measurements(
                device_id, measurement_type="c8y_NonExistentType"
            )

            # Should return valid structure
            assert "measurements" in result
            assert isinstance(result["measurements"], list)
