"""Agent wiring for PPT workflows using claude-agent-sdk."""
from __future__ import annotations

from typing import AsyncIterator

from claude_agent_sdk import ClaudeAgentOptions, Message, ResultMessage, create_sdk_mcp_server, query

from .config import settings
from .skills import create_ppt_visuals, draft_ppt_outline

ppt_server = create_sdk_mcp_server(
    name="ppt-skills",
    version="1.0.0",
    tools=[draft_ppt_outline, create_ppt_visuals],
)


async def run_agent(prompt: str) -> AsyncIterator[Message]:
    """Run the Claude agent with the PPT-focused MCP server."""

    options = ClaudeAgentOptions(
        system_prompt=settings.system_prompt,
        model=settings.default_text_model,
        mcp_servers={"ppt": ppt_server},
        allowed_tools=["draft_ppt_outline", "create_ppt_visuals"],
        permission_mode="bypassPermissions",
    )

    async for message in query(prompt=prompt, options=options):
        yield message


async def summarize_run(prompt: str) -> dict:
    """Convenience helper that collects the result message."""

    summary: dict = {"messages": []}
    async for message in run_agent(prompt):
        if isinstance(message, ResultMessage):
            summary["cost"] = getattr(message, "total_cost_usd", None)
        summary["messages"].append(message)
    return summary
