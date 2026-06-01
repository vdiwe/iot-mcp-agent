"""
examples/fleet_health_report.py

Demonstrates a one-shot agent that generates a natural language
fleet health report across all device groups.

Run:
    python examples/fleet_health_report.py
"""

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from iot_mcp_agent.agents.base_agent import BaseAgent  # type: ignore[import-untyped]

logging.basicConfig(level=logging.WARNING)  # Quieter for this demo


GOAL = """
Generate a complete Fleet Health Report for all IoT devices.

Steps:
1. Get a summary for each of these device groups:
   - Factory Floor
   - Pump Station
   - Warehouse
   - Network
2. For any group with offline devices, list which devices are offline
3. Check for any active alarms across all devices
4. Get vibration readings for all motors in the Pump Station and flag
   any showing upward trends (possible bearing wear)
5. Produce a well-structured Fleet Health Report with:
   - Executive summary (2-3 sentences)
   - Group-by-group status table
   - Anomalies requiring immediate attention
   - Anomalies to monitor
   - Recommended actions with priority (High / Medium / Low)

Format the report clearly — it will be sent to the Plant Manager.
"""


async def main():
    print("\n" + "=" * 60)
    print("  IoT Fleet Health Report Agent")
    print("=" * 60 + "\n")

    agent = BaseAgent(platform="simulate", max_iterations=30)
    run = await agent.run_once(GOAL)

    print("\n" + "=" * 60)
    print("  FLEET HEALTH REPORT")
    print("=" * 60)
    print(run.final_summary)
    print("\n" + "=" * 60)
    print(f"Report generated in {run.duration_seconds():.1f}s | {run.iterations} reasoning steps")


if __name__ == "__main__":
    asyncio.run(main())
