from dataclasses import dataclass, field


@dataclass
class ToolCallRecord:
    name: str
    input: dict
    output: str


@dataclass
class AgentTurnResult:
    reply: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    raw_messages: list[dict] = field(default_factory=list)
    hit_turn_limit: bool = False
