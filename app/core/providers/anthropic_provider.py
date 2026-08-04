from app.core.providers.base import Provider, ProviderTurnResult
from app.core.agent_types import ToolCallRecord
from app.core.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self):
        self._client = None
        if ANTHROPIC_API_KEY:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def run_turn(self, system_prompt, tools, tool_impl, conversation, max_turns):
        if self._client is None:
            return ProviderTurnResult(
                reply=(
                    "[Server misconfigured: ANTHROPIC_API_KEY is not set. "
                    "Ask the app operator to export it and restart.]"
                ),
                tool_calls=[],
                raw_messages=conversation,
            )

        messages = list(conversation)
        tool_calls: list[ToolCallRecord] = []

        try:
            for _ in range(max_turns):
                response = self._client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=1024,
                    system=system_prompt,
                    tools=tools,
                    messages=messages,
                )
                messages.append({"role": "assistant", "content": response.content})

                if response.stop_reason != "tool_use":
                    text = "".join(b.text for b in response.content if b.type == "text")
                    return ProviderTurnResult(reply=text, tool_calls=tool_calls, raw_messages=messages)

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        output = _invoke(tool_impl, block.name, block.input)
                        tool_calls.append(ToolCallRecord(name=block.name, input=block.input, output=str(output)))
                        tool_results.append(
                            {"type": "tool_result", "tool_use_id": block.id, "content": str(output)}
                        )
                messages.append({"role": "user", "content": tool_results})
        except Exception as e:  # noqa: BLE001
            return ProviderTurnResult(
                reply=(
                    f"[Anthropic API error: {e}. Check that ANTHROPIC_API_KEY in your "
                    ".env is a real, valid key (not the placeholder) and that your "
                    "account has available credit.]"
                ),
                tool_calls=tool_calls,
                raw_messages=messages,
            )

        return ProviderTurnResult(
            reply="[Max tool-call turns reached for this message.]",
            tool_calls=tool_calls,
            raw_messages=messages,
            hit_turn_limit=True,
        )


def _invoke(tool_impl, name, input_dict):
    impl = tool_impl.get(name)
    if impl is None:
        return f"Error: no implementation for tool '{name}'"
    try:
        return impl(input_dict)
    except Exception as e:  # noqa: BLE001
        return f"Tool execution error: {e}"
