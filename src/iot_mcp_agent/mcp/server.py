"""
iot_mcp_agent/mcp/server.py

MCP Server that exposes IoT platform capabilities as tools.
Supports Cumulocity IoT, AWS IoT Core, Azure IoT Hub, and a built-in simulator.
"""

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from iot_mcp_agent.tools.action_tools import ActionTools
from iot_mcp_agent.tools.alarm_tools import AlarmTools
from iot_mcp_agent.tools.device_tools import DeviceTools

from ..config import Settings
from ..utils.simulator import DeviceSimulator

logger = logging.getLogger(__name__)
settings = Settings()


def build_server(platform: str = "simulate") -> Server:
    """
    Build and configure the MCP server with all IoT tools.

    Args:
        platform: One of 'cumulocity', 'aws_iot', 'azure_iot', 'simulate'

    Returns:
        Configured MCP Server instance
    """
    server = Server("iot-mcp-agent")

    # Initialise platform adapter
    adapter: Any
    if platform == "simulate":
        adapter = DeviceSimulator()
        logger.info("Running with simulated IoT devices")
    elif platform == "cumulocity":
        from ..platforms.cumulocity import CumulocityAdapter

        adapter = CumulocityAdapter(
            base_url=settings.c8y_base_url,
            username=settings.c8y_username,
            password=settings.c8y_password,
        )
        logger.info("Connected to Cumulocity IoT: %s", settings.c8y_base_url)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    device_tools = DeviceTools(adapter)
    alarm_tools = AlarmTools(adapter)
    action_tools = ActionTools(adapter)

    # ── Tool Definitions ────────────────────────────────────────────────────

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_devices",
                description=(
                    "List all IoT devices. Optionally filter by group, type, or status. "
                    "Returns device IDs, names, types, and online/offline status."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group": {"type": "string", "description": "Filter by device group name"},
                        "device_type": {"type": "string", "description": "Filter by device type"},
                        "status": {
                            "type": "string",
                            "enum": ["AVAILABLE", "UNAVAILABLE", "MAINTENANCE"],
                            "description": "Filter by availability status",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 50,
                            "description": "Max devices to return",
                        },
                    },
                },
            ),
            Tool(
                name="get_device",
                description=(
                    "Get detailed information about a specific device including its "
                    "current status, last communication time, and configuration."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "The device ID"},
                    },
                    "required": ["device_id"],
                },
            ),
            Tool(
                name="get_measurements",
                description=(
                    "Retrieve time-series measurement data (telemetry) for a device. "
                    "Supports filtering by measurement type and time range. "
                    "Use this to analyse trends, detect anomalies, or compare to baselines."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "The device ID"},
                        "measurement_type": {
                            "type": "string",
                            "description": "E.g. 'c8y_Temperature', 'c8y_Vibration'",
                        },
                        "from_time": {"type": "string", "description": "ISO 8601 start time"},
                        "to_time": {"type": "string", "description": "ISO 8601 end time"},
                        "limit": {"type": "integer", "default": 100},
                    },
                    "required": ["device_id"],
                },
            ),
            Tool(
                name="get_alarms",
                description=(
                    "Get active or historical alarms for a device or across all devices. "
                    "Returns alarm severity, status, and description."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Device ID (omit for all devices)",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["CRITICAL", "MAJOR", "MINOR", "WARNING"],
                        },
                        "status": {"type": "string", "enum": ["ACTIVE", "ACKNOWLEDGED", "CLEARED"]},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            Tool(
                name="create_alarm",
                description=(
                    "Create a new alarm on a device. Use when the agent detects a problem "
                    "that requires human attention or automated response."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                        "type": {
                            "type": "string",
                            "description": "Alarm type, e.g. 'c8y_TemperatureAlarm'",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["CRITICAL", "MAJOR", "MINOR", "WARNING"],
                        },
                        "text": {
                            "type": "string",
                            "description": "Human-readable alarm description",
                        },
                    },
                    "required": ["device_id", "type", "severity", "text"],
                },
            ),
            Tool(
                name="update_device_config",
                description=(
                    "Update a device configuration property remotely. "
                    "For example, change reporting interval, thresholds, or operating mode."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                        "config_key": {
                            "type": "string",
                            "description": "Configuration property name",
                        },
                        "config_value": {"description": "New value for the property"},
                        "reason": {
                            "type": "string",
                            "description": "Reason for this change (for audit log)",
                        },
                    },
                    "required": ["device_id", "config_key", "config_value", "reason"],
                },
            ),
            Tool(
                name="send_notification",
                description=(
                    "Send a notification (email, SMS, or Slack) to a team or individual. "
                    "Use for escalations, reports, or status updates."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string", "enum": ["email", "slack", "sms"]},
                        "recipient": {
                            "type": "string",
                            "description": "Email address, Slack channel, or phone",
                        },
                        "subject": {"type": "string"},
                        "message": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high", "urgent"],
                            "default": "normal",
                        },
                    },
                    "required": ["channel", "recipient", "subject", "message"],
                },
            ),
            Tool(
                name="get_device_group_summary",
                description=(
                    "Get an aggregated health summary for all devices in a group. "
                    "Returns counts of online/offline devices, active alarms, and average metrics."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_name": {"type": "string", "description": "Device group name"},
                    },
                    "required": ["group_name"],
                },
            ),
        ]

    # ── Tool Handlers ────────────────────────────────────────────────────────

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        logger.debug("Tool called: %s with args: %s", name, arguments)

        try:
            if name == "list_devices":
                result = await device_tools.list_devices(**arguments)
            elif name == "get_device":
                result = await device_tools.get_device(**arguments)
            elif name == "get_measurements":
                result = await device_tools.get_measurements(**arguments)
            elif name == "get_alarms":
                result = await alarm_tools.get_alarms(**arguments)
            elif name == "create_alarm":
                result = await alarm_tools.create_alarm(**arguments)
            elif name == "update_device_config":
                result = await action_tools.update_device_config(**arguments)
            elif name == "send_notification":
                result = await action_tools.send_notification(**arguments)
            elif name == "get_device_group_summary":
                result = await device_tools.get_device_group_summary(**arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}

        except Exception as exc:
            logger.exception("Tool %s failed: %s", name, exc)
            result = {"error": str(exc)}

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    return server


async def main(platform: str = "simulate") -> None:
    server = build_server(platform)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    import sys

    _platform = sys.argv[1] if len(sys.argv) > 1 else "simulate"
    asyncio.run(main(_platform))
