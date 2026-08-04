"""
Every scenario module (app/scenarios/llmXX_.../scenario.py) must expose a
module-level `SCENARIO` instance of this dataclass.
"""

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Scenario:
    id: str                      # e.g. "llm01_prompt_injection"
    owasp_id: str                # e.g. "LLM01:2025"
    title: str                   # e.g. "Prompt Injection"
    difficulty: str              # "Beginner" | "Intermediate" | "Advanced"
    tagline: str                 # one-line description for the menu card
    objective_md: str            # markdown shown in the "Objective" panel
    hints_md: str                # markdown shown behind a "Show hints" toggle
    fix_md: str                  # markdown shown after the flag is captured
    system_prompt: str
    tools: list[dict]
    tool_impl_factory: Callable[[dict], dict[str, Any]]
    # tool_impl_factory(scenario_state) -> {tool_name: callable(input_dict) -> str}
    # scenario_state is a plain dict, unique per (session_id, scenario_id),
    # so each scenario can stash mutable fake "server-side" state there.
    initial_state: Callable[[], dict] = field(default=lambda: {})
    check_flag: Callable[[dict, list, str], str | None] = field(
        default=lambda state, tool_calls, reply_text: None
    )
    # check_flag(scenario_state, tool_calls_this_turn, assistant_reply_text) -> flag string or None
