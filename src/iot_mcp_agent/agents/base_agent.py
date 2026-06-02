"""
iot_mcp_agent/agents/base_agent.py

Core agentic reasoning loop.

The agent:
  1. Receives a goal in natural language
  2. Calls the LLM with available MCP tools
  3. Executes tool calls via the MCP client
  4. Feeds results back to the LLM
  5. Repeats until the LLM declares the goal complete
  6. Returns a structured summary of actions taken
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent as MCPTextContent

from ..config import Settings
from ..llm.factory import create_llm_adapter

logger = logging.getLogger(__name__)
settings = Settings()


@dataclass
class AgentRun:
    """Record of a single agent run."""

    goal: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    iterations: int = 0
    tools_called: list[dict] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    final_summary: str = ""
    success: bool = False

    def duration_seconds(self) -> float:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0.0


class BaseAgent:
    """
    Agentic loop that connects an LLM to IoT tools via MCP.

    The agent runs a ReAct-style loop:
      Think → Act (tool call) → Observe (result) → Think → ...
    until the model produces a final answer.
    """

    SYSTEM_PROMPT = """You are an expert Industrial IoT operations agent.

You have access to tools that let you interact with a live IoT platform:
- Query device status, telemetry, and alarms
- Create alarms for anomalies you detect
- Update device configurations
- Send notifications to operations teams

Your job is to accomplish the user's goal autonomously and thoroughly.

Guidelines:
- Always start by gathering information before taking any action
- Think step by step. Reason about what you observe before deciding what to do
- When you detect a problem, investigate it fully (check history, neighbours, trends)
- Be conservative with actions that change device state — only act when confident
- Every action you take should be logged with a clear reason
- When you are done, provide a clear, concise summary of:
  * What you found
  * What actions you took (and why)
  * Any recommendations for the operations team
"""

    def __init__(
        self,
        platform: str = "simulate",
        max_iterations: int = 20,
        model: str | None = None,
    ):
        self.platform = platform
        self.max_iterations = max_iterations
        self.model = model or settings.llm_model
        self.llm = create_llm_adapter(
            system_prompt=self.SYSTEM_PROMPT,
            model=self.model,
            settings=settings,
        )

    async def run_once(self, goal: str) -> AgentRun:
        """
        Execute the agent for a single goal.

        Args:
            goal: Natural language description of what the agent should do.

        Returns:
            AgentRun with full record of what happened.
        """
        run = AgentRun(goal=goal)
        logger.info("Agent starting. Goal: %s", goal)

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "iot_mcp_agent.mcp.server", self.platform],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Fetch available tools from the MCP server
                tools_response = await session.list_tools()
                tools: list[Any] = self.llm.format_tools(tools_response.tools)

                messages: list[Any] = [self.llm.make_user_message(goal)]

                for iteration in range(self.max_iterations):
                    run.iterations = iteration + 1
                    logger.debug("Iteration %d/%d", run.iterations, self.max_iterations)

                    llm_response = await self.llm.chat(messages, tools)

                    # Append assistant turn to history
                    messages.append(self.llm.make_assistant_message(llm_response.raw))

                    # No tool calls → agent has finished
                    if not llm_response.tool_calls:
                        run.final_summary = llm_response.final_text or ""
                        run.success = True
                        logger.info("Agent completed after %d iterations", run.iterations)
                        break

                    # Execute all tool calls the LLM requested
                    results: dict[str, str] = {}
                    for tc in llm_response.tool_calls:
                        logger.info("Calling tool: %s(%s)", tc.name, json.dumps(tc.input))

                        run.tools_called.append(
                            {
                                "iteration": run.iterations,
                                "tool": tc.name,
                                "input": tc.input,
                            }
                        )

                        try:
                            result = await session.call_tool(tc.name, tc.input)
                            first = result.content[0] if result.content else None
                            results[tc.id] = (
                                first.text if isinstance(first, MCPTextContent) else "{}"
                            )
                        except Exception as exc:
                            results[tc.id] = json.dumps({"error": str(exc)})
                            logger.warning("Tool %s failed: %s", tc.name, exc)

                        if tc.name in (
                            "create_alarm",
                            "update_device_config",
                            "send_notification",
                        ):
                            run.actions_taken.append(f"[{tc.name}] {json.dumps(tc.input)}")

                    messages.extend(
                        self.llm.make_tool_results_message(llm_response.tool_calls, results)
                    )

                else:
                    logger.warning("Agent hit max iterations (%d)", self.max_iterations)
                    run.final_summary = "Max iterations reached before goal completion."

        run.finished_at = datetime.now(UTC)
        logger.info(
            "Run complete. Duration: %.1fs | Iterations: %d | Tools called: %d | Actions: %d",
            run.duration_seconds(),
            run.iterations,
            len(run.tools_called),
            len(run.actions_taken),
        )
        return run
