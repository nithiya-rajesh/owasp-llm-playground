"""
Thin, provider-agnostic dispatcher. All the actual API-shape translation
lives in app/core/providers/*. Scenario code and app/main.py only ever see
ToolCallRecord / AgentTurnResult from here, regardless of which backend is
configured via MODEL_PROVIDER.
"""

from app.core.agent_types import ToolCallRecord, AgentTurnResult
from app.core.providers import get_provider
from app.core.config import MAX_TOOL_TURNS


def run_agent_turn(
    system_prompt: str,
    tools: list[dict],
    tool_impl: dict,
    conversation: list[dict],
    max_turns: int = MAX_TOOL_TURNS,
) -> AgentTurnResult:
    provider = get_provider()
    result = provider.run_turn(
        system_prompt=system_prompt,
        tools=tools,
        tool_impl=tool_impl,
        conversation=conversation,
        max_turns=max_turns,
    )
    return AgentTurnResult(
        reply=result.reply,
        tool_calls=result.tool_calls,
        raw_messages=result.raw_messages,
        hit_turn_limit=result.hit_turn_limit,
    )
