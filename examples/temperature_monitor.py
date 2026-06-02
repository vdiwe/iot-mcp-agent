"""
examples/temperature_monitor.py

Demonstrates a one-shot diagnostic agent that finds temperature anomalies,
investigates them, and creates alarms + notifications autonomously.

Run:
    python examples/temperature_monitor.py
"""

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from iot_mcp_agent.agents.base_agent import BaseAgent  # type: ignore[import-untyped]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


GOAL = """
You are monitoring a factory floor with 8 temperature sensors.

Your task:
1. List all temperature sensors and check which are online
2. Get the latest 20 measurements for EACH online sensor
3. Identify any sensors showing abnormal temperature readings
   - Normal operating range: 15°C to 40°C
   - Warning threshold: 40°C to 60°C
   - Critical threshold: above 60°C
4. For any sensor above the warning threshold:
   a. Get its last 50 readings to understand the trend
   b. Check if there are any existing alarms for that device
5. Create appropriate alarms (WARNING or CRITICAL) for anomalous sensors
6. Send an email notification to ops-team@factory.com summarising findings
7. Provide a complete report: which sensors are normal, which are concerning,
   what actions you took, and your recommendations
"""


async def main():
    print("\n" + "=" * 60)
    print("  IoT Temperature Monitoring Agent (Simulated)")
    print("=" * 60 + "\n")

    agent = BaseAgent(platform="simulate", max_iterations=25)

    print(f"Goal: {GOAL[:120]}...\n")
    print("Agent running...\n")

    run = await agent.run_once(GOAL)

    print("\n" + "=" * 60)
    print("  AGENT RUN COMPLETE")
    print("=" * 60)
    print(f"  Duration:   {run.duration_seconds():.1f}s")
    print(f"  Iterations: {run.iterations}")
    print(f"  Tools used: {len(run.tools_called)}")
    print(f"  Actions:    {len(run.actions_taken)}")
    print(f"  Success:    {'✅' if run.success else '⚠️ '}")

    if run.actions_taken:
        print("\nActions taken:")
        for action in run.actions_taken:
            print(f"  → {action}")

    print("\nAgent Summary:")
    print("-" * 40)
    print(run.final_summary)


if __name__ == "__main__":
    asyncio.run(main())
