"""Tests for iot_mcp_agent.utils.simulator module."""

import pytest

from iot_mcp_agent.utils.simulator import DeviceSimulator


@pytest.fixture
def simulator():
    """Create a DeviceSimulator instance for testing."""
    return DeviceSimulator()


class TestDeviceSimulator:
    """Test suite for DeviceSimulator."""

    @pytest.mark.asyncio
    async def test_simulator_initialization(self, simulator):
        """Test simulator initializes with devices."""
        devices = await simulator.list_devices()

        assert devices is not None
        assert "total" in devices
        assert "devices" in devices
        assert devices["total"] > 0
        assert len(devices["devices"]) > 0

    @pytest.mark.asyncio
    async def test_list_devices_basic(self, simulator):
        """Test listing devices without filters."""
        result = await simulator.list_devices()

        assert result["total"] >= 0
        for device in result["devices"]:
            assert "id" in device
            assert "name" in device
            assert "type" in device
            assert "status" in device

    @pytest.mark.asyncio
    async def test_list_devices_with_status_filter(self, simulator):
        """Test listing devices filtered by status."""
        result = await simulator.list_devices(status="AVAILABLE")

        assert result["total"] >= 0
        for device in result["devices"]:
            assert device["status"] == "AVAILABLE"

    @pytest.mark.asyncio
    async def test_list_devices_with_limit(self, simulator):
        """Test listing devices with limit parameter."""
        result = await simulator.list_devices(limit=5)

        assert len(result["devices"]) <= 5

    @pytest.mark.asyncio
    async def test_get_device(self, simulator):
        """Test retrieving a specific device."""
        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]
            result = await simulator.get_device(device_id)

            assert result["id"] == device_id
            assert "name" in result
            assert "type" in result

    @pytest.mark.asyncio
    async def test_get_measurements(self, simulator):
        """Test retrieving measurements for a device."""
        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]
            result = await simulator.get_measurements(device_id)

            assert "measurements" in result
            for measurement in result["measurements"]:
                assert "timestamp" in measurement
                assert "type" in measurement
                assert "value" in measurement

    @pytest.mark.asyncio
    async def test_get_measurements_with_type_filter(self, simulator):
        """Test retrieving specific measurement types."""
        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]
            result = await simulator.get_measurements(
                device_id, measurement_type="c8y_Temperature"
            )

            for measurement in result["measurements"]:
                assert measurement["type"] == "c8y_Temperature"

    @pytest.mark.asyncio
    async def test_get_measurements_with_limit(self, simulator):
        """Test measurement limit parameter."""
        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]
            result = await simulator.get_measurements(device_id, limit=10)

            assert len(result["measurements"]) <= 10

    @pytest.mark.asyncio
    async def test_get_alarms(self, simulator):
        """Test retrieving alarms."""
        result = await simulator.get_alarms()

        assert "total" in result
        assert "alarms" in result
        assert isinstance(result["alarms"], list)

    @pytest.mark.asyncio
    async def test_get_alarms_with_device_filter(self, simulator):
        """Test retrieving alarms filtered by device."""
        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]
            result = await simulator.get_alarms(device_id=device_id)

            for alarm in result["alarms"]:
                assert alarm["device_id"] == device_id

    @pytest.mark.asyncio
    async def test_get_alarms_with_severity_filter(self, simulator):
        """Test retrieving alarms filtered by severity."""
        result = await simulator.get_alarms(severity="CRITICAL")

        for alarm in result["alarms"]:
            assert alarm["severity"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_create_alarm(self, simulator):
        """Test creating an alarm."""
        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]
            result = await simulator.create_alarm(
                device_id=device_id,
                type="c8y_TestAlarm",
                severity="MAJOR",
                text="Test alarm for unit testing",
            )

            assert result["success"] is True
            assert result["alarm"]["device_id"] == device_id
            assert result["alarm"]["severity"] == "MAJOR"
            assert result["alarm"]["text"] == "Test alarm for unit testing"
            assert "alarm_id" in result

    @pytest.mark.asyncio
    async def test_update_device_config(self, simulator):
        """Test updating device configuration."""
        devices = await simulator.list_devices(limit=1)
        if devices["devices"]:
            device_id = devices["devices"][0]["id"]
            result = await simulator.update_device_config(
                device_id=device_id,
                config_key="reporting_interval",
                config_value="30",
                reason="Testing config update",
            )

            assert result["device_id"] == device_id
            assert result["updated"]["reporting_interval"] == "30"

    @pytest.mark.asyncio
    async def test_get_device_group_summary(self, simulator):
        """Test retrieving device group summary."""
        result = await simulator.get_device_group_summary("Factory Floor")

        assert "group" in result
        assert "total_devices" in result
        assert "online" in result
        assert "offline" in result
        assert "maintenance" in result
