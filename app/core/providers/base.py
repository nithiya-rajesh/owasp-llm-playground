"""
Every provider translates between OUR internal shape (plain dicts/dataclasses,
already used throughout app/scenarios/*) and whatever dialect its API speaks.

Internal shapes (defined here, used everywhere else):
  - a tool definition: {"name": str, "description": str, "input_schema": dict (JSON Schema)}
  - a tool call the model wants to make: {"name": str, "input": dict}
  - a tool result we send back: {"name": str, "output": str}

Scenario authors never need to know which provider is active — scenario.py
files only ever see ToolCallRecord / AgentTurnResult from app.core.agent.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderTurnResult:
    reply: str
    tool_calls: list  # list of ToolCallRecord-shaped objects, see app/core/agent.py
    raw_messages: list  # provider-native message history, opaque to callers
    hit_turn_limit: bool = False


class Provider(ABC):
    """One instance per configured backend (Anthropic, Gemini, Ollama, ...)."""

    name: str

    @abstractmethod
    def run_turn(
        self,
        system_prompt: str,
        tools: list[dict],
        tool_impl: dict,
        conversation: list[dict],
        max_turns: int,
    ) -> ProviderTurnResult:
        """
        conversation is in OUR neutral shape: a list of
          {"role": "user" | "assistant", "content": str}
        for plain turns, PLUS whatever provider-native turns this same
        provider appended in a previous call (each provider only ever reads
        back its own native history, so this is safe — the app always keeps
        conversation history is per-session and per-provider).
        """
        raise NotImplementedError
