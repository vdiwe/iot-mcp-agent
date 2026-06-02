"""CLI entrypoint for iot_mcp_agent."""

import argparse
import asyncio
import logging

try:
    from .agents.base_agent import BaseAgent
except ImportError:
    # Support direct execution: python src/iot_mcp_agent/__main__.py
    import os
    import sys

    package_dir = os.path.dirname(__file__)
    if sys.path and os.path.abspath(sys.path[0]) == os.path.abspath(package_dir):
        sys.path.pop(0)

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from iot_mcp_agent.agents.base_agent import BaseAgent


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the IoT MCP agent")
    parser.add_argument(
        "--goal",
        default="List all devices and provide a brief health summary.",
        help="Natural language goal for the agent run",
    )
    parser.add_argument(
        "--platform",
        default="simulate",
        help="IoT platform backend (e.g. simulate, cumulocity)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Maximum reasoning iterations",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    return parser.parse_args()


async def _run() -> int:
    args = _parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    agent = BaseAgent(
        platform=args.platform,
        max_iterations=args.max_iterations,
    )
    result = await agent.run_once(args.goal)

    print(result.final_summary)
    return 0 if result.success else 1


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
