"""
iot_mcp_agent/agents/monitor_agent.py

Continuous monitoring agent — runs the agentic loop on a schedule,
persisting state between runs so it can track trends over time.
"""

import asyncio
import logging
import signal
from datetime import datetime

from .base_agent import BaseAgent, AgentRun
from ..config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


class MonitorAgent(BaseAgent):
    """
    Runs the base agent on a recurring schedule.

    Unlike a one-shot agent, MonitorAgent:
    - Runs continuously at a configurable interval
    - Keeps a history of past runs for trend analysis
    - Can escalate if the same issue recurs across multiple runs
    - Gracefully handles shutdown signals
    """

    def __init__(
        self,
        goal: str,
        check_interval_seconds: int = 60,
        platform: str = "simulate",
        max_run_history: int = 100,
        **kwargs,
    ):
        super().__init__(platform=platform, **kwargs)
        self.goal = goal
        self.check_interval_seconds = check_interval_seconds
        self.max_run_history = max_run_history
        self.run_history: list[AgentRun] = []
        self._running = False

    async def run(self) -> None:
        """Start the continuous monitoring loop."""
        self._running = True
        self._setup_signal_handlers()

        logger.info(
            "MonitorAgent started. Interval: %ds | Goal: %s",
            self.check_interval_seconds,
            self.goal,
        )

        run_count = 0
        while self._running:
            run_count += 1
            logger.info("─── Monitor run #%d ───", run_count)

            try:
                run = await self.run_once(self._build_goal_with_context())
                self._record_run(run)
                self._log_run_summary(run)
            except Exception as exc:
                logger.exception("Monitor run #%d failed: %s", run_count, exc)

            if self._running:
                logger.info("Sleeping %ds until next check...", self.check_interval_seconds)
                await asyncio.sleep(self.check_interval_seconds)

        logger.info("MonitorAgent stopped after %d runs.", run_count)

    def stop(self) -> None:
        """Gracefully stop the monitoring loop."""
        logger.info("Stopping MonitorAgent...")
        self._running = False

    def _build_goal_with_context(self) -> str:
        """Enrich the goal with context from recent run history."""
        context_lines = [self.goal]

        if self.run_history:
            last = self.run_history[-1]
            context_lines.append(
                f"\n--- Context from last run at {last.started_at.isoformat()} ---"
            )
            if last.actions_taken:
                context_lines.append("Actions taken in last run:")
                for action in last.actions_taken[-5:]:  # last 5 actions
                    context_lines.append(f"  - {action}")
            if last.final_summary:
                context_lines.append(f"Last summary: {last.final_summary[:300]}")

        return "\n".join(context_lines)

    def _record_run(self, run: AgentRun) -> None:
        self.run_history.append(run)
        if len(self.run_history) > self.max_run_history:
            self.run_history.pop(0)

    def _log_run_summary(self, run: AgentRun) -> None:
        status = "✅ SUCCESS" if run.success else "⚠️  INCOMPLETE"
        logger.info(
            "%s | Duration: %.1fs | Iterations: %d | Tools: %d | Actions: %d",
            status, run.duration_seconds(), run.iterations,
            len(run.tools_called), len(run.actions_taken),
        )
        if run.actions_taken:
            logger.info("Actions taken:")
            for action in run.actions_taken:
                logger.info("  → %s", action)
        if run.final_summary:
            logger.info("Summary: %s", run.final_summary[:500])

    def _setup_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.stop)
