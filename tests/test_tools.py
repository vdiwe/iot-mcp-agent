"""Tests for iot_mcp_agent.tools module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iot_mcp_agent.tools.action_tools import ActionTools
from iot_mcp_agent.tools.alarm_tools import AlarmTools
from iot_mcp_agent.tools.device_tools import DeviceTools


@pytest.fixture
def mock_adapter():
    """Create a mock adapter."""
    adapter = AsyncMock()
    return adapter


class TestDeviceTools:
    """Test suite for DeviceTools."""

    @pytest.mark.asyncio
    async def test_list_devices(self, mock_adapter):
        """Test listing devices through DeviceTools."""
        mock_adapter.list_devices.return_value = {
            "total": 2,
            "devices": [
                {"id": "device-001", "name": "Sensor A", "status": "AVAILABLE"},
                {"id": "device-002", "name": "Sensor B", "status": "UNAVAILABLE"},
            ],
        }

        tools = DeviceTools(mock_adapter)
        result = await tools.list_devices()

        assert result["total"] == 2
        assert len(result["devices"]) == 2
        mock_adapter.list_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_devices_with_filters(self, mock_adapter):
        """Test listing devices with filters."""
        mock_adapter.list_devices.return_value = {
            "total": 1,
            "devices": [
                {"id": "device-001", "name": "Sensor A", "status": "AVAILABLE"},
            ],
        }

        tools = DeviceTools(mock_adapter)
        result = await tools.list_devices(status="AVAILABLE", limit=10)

        assert result["total"] == 1
        mock_adapter.list_devices.assert_called_once_with(
            group=None,
            device_type=None,
            status="AVAILABLE", limit=10
        )

    @pytest.mark.asyncio
    async def test_get_device(self, mock_adapter):
        """Test retrieving a specific device."""
        mock_adapter.get_device.return_value = {
            "id": "device-001",
            "name": "Sensor A",
            "type": "c8y_TemperatureSensor",
            "status": "AVAILABLE",
        }

        tools = DeviceTools(mock_adapter)
        result = await tools.get_device("device-001")

        assert result["id"] == "device-001"
        assert result["name"] == "Sensor A"
        mock_adapter.get_device.assert_called_once_with("device-001")

    @pytest.mark.asyncio
    async def test_get_measurements(self, mock_adapter):
        """Test retrieving measurements."""
        mock_adapter.get_measurements.return_value = {
            "total": 3,
            "measurements": [
                {"timestamp": "2026-06-02T10:00:00Z", "value": 25.5, "unit": "°C"},
                {"timestamp": "2026-06-02T10:01:00Z", "value": 25.7, "unit": "°C"},
                {"timestamp": "2026-06-02T10:02:00Z", "value": 26.0, "unit": "°C"},
            ],
        }

        tools = DeviceTools(mock_adapter)
        result = await tools.get_measurements("device-001")

        assert result["total"] == 3
        assert len(result["measurements"]) == 3
        mock_adapter.get_measurements.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_device_group_summary(self, mock_adapter):
        """Test retrieving device group summary."""
        mock_adapter.get_device_group_summary.return_value = {
            "group_name": "Factory Floor",
            "online_count": 8,
            "offline_count": 2,
            "avg_temperature": 35.2,
        }

        tools = DeviceTools(mock_adapter)
        result = await tools.get_device_group_summary("Factory Floor")

        assert result["group_name"] == "Factory Floor"
        assert result["online_count"] == 8
        mock_adapter.get_device_group_summary.assert_called_once_with("Factory Floor")


class TestAlarmTools:
    """Test suite for AlarmTools."""

    @pytest.mark.asyncio
    async def test_get_alarms(self, mock_adapter):
        """Test retrieving alarms."""
        mock_adapter.get_alarms.return_value = {
            "total": 2,
            "alarms": [
                {
                    "id": "alarm-001",
                    "device_id": "device-001",
                    "severity": "CRITICAL",
                    "status": "ACTIVE",
                },
                {
                    "id": "alarm-002",
                    "device_id": "device-002",
                    "severity": "MAJOR",
                    "status": "ACTIVE",
                },
            ],
        }

        tools = AlarmTools(mock_adapter)
        result = await tools.get_alarms()

        assert result["total"] == 2
        assert len(result["alarms"]) == 2
        mock_adapter.get_alarms.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_alarms_with_filters(self, mock_adapter):
        """Test retrieving alarms with filters."""
        mock_adapter.get_alarms.return_value = {
            "total": 1,
            "alarms": [
                {
                    "id": "alarm-001",
                    "device_id": "device-001",
                    "severity": "CRITICAL",
                    "status": "ACTIVE",
                }
            ],
        }

        tools = AlarmTools(mock_adapter)
        result = await tools.get_alarms(device_id="device-001", severity="CRITICAL")

        assert result["total"] == 1
        mock_adapter.get_alarms.assert_called_once_with(
            device_id="device-001", severity="CRITICAL", status=None, limit=20
        )

    @pytest.mark.asyncio
    async def test_create_alarm(self, mock_adapter):
        """Test creating an alarm."""
        mock_adapter.create_alarm.return_value = {
            "id": "alarm-new-001",
            "device_id": "device-001",
            "type": "c8y_TemperatureAlarm",
            "severity": "CRITICAL",
            "text": "Temperature exceeds 60°C",
            "status": "ACTIVE",
        }

        tools = AlarmTools(mock_adapter)
        result = await tools.create_alarm(
            device_id="device-001",
            type="c8y_TemperatureAlarm",
            severity="CRITICAL",
            text="Temperature exceeds 60°C",
        )

        assert result["device_id"] == "device-001"
        assert result["severity"] == "CRITICAL"
        mock_adapter.create_alarm.assert_called_once()


class TestActionTools:
    """Test suite for ActionTools."""

    @pytest.mark.asyncio
    async def test_update_device_config(self, mock_adapter):
        """Test updating device configuration."""
        mock_adapter.update_device_config.return_value = {
            "device_id": "device-001",
            "config_key": "reporting_interval",
            "config_value": "30",
            "success": True,
        }

        tools = ActionTools(mock_adapter)
        result = await tools.update_device_config(
            device_id="device-001",
            config_key="reporting_interval",
            config_value="30",
            reason="Increase data collection frequency",
        )

        assert result["device_id"] == "device-001"
        assert result["config_value"] == "30"
        mock_adapter.update_device_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_email(self, mock_adapter):
        """Test sending an email notification."""
        mock_adapter.send_notification.return_value = {
            "channel": "email",
            "recipient": "ops-team@factory.com",
            "status": "sent",
        }

        tools = ActionTools(mock_adapter)
        result = await tools.send_notification(
            channel="email",
            recipient="ops-team@factory.com",
            subject="Temperature Alert",
            message="Critical temperature detected",
        )

        assert result["channel"] == "email"
        assert result["status"] == "sent"
        mock_adapter.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_slack(self, mock_adapter):
        """Test sending a Slack notification."""
        mock_adapter.send_notification.return_value = {
            "channel": "slack",
            "recipient": "#operations",
            "status": "sent",
        }

        tools = ActionTools(mock_adapter)
        result = await tools.send_notification(
            channel="slack",
            recipient="#operations",
            subject="Alert",
            message="Device offline",
        )

        assert result["channel"] == "slack"
        mock_adapter.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_with_priority(self, mock_adapter):
        """Test sending notification with priority level."""
        mock_adapter.send_notification.return_value = {
            "status": "sent",
            "priority": "urgent",
        }

        tools = ActionTools(mock_adapter)
        result = await tools.send_notification(
            channel="email",
            recipient="admin@factory.com",
            subject="Critical Alert",
            message="System failure",
            priority="urgent",
        )

        assert result["priority"] == "urgent"
        mock_adapter.send_notification.assert_called_once()
