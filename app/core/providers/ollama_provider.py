"""
Ollama exposes an OpenAI-compatible endpoint at {OLLAMA_HOST}/v1, so we reuse
the `openai` SDK rather than writing raw HTTP calls. Tool-calling format here
follows OpenAI's convention: tools are {"type": "function", "function": {...}},
and a model turn wanting a tool call returns `message.tool_calls`, each with
a JSON-string `arguments` field we must parse ourselves.

Local/small models are noticeably less reliable at emitting well-formed tool
calls than Claude or Gemini — this file does not attempt to compensate for
that; it surfaces whatever the model actually does, which is the honest
training signal a learner should see.
"""

import json
from app.core.providers.base import Provider, ProviderTurnResult
from app.core.agent_types import ToolCallRecord
from app.core.config import OLLAMA_HOST, OLLAMA_MODEL


def _to_openai_tools(tools: list[dict]):
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self):
        from openai import OpenAI
        # Ollama ignores the API key but the SDK requires a non-empty string.
        self._client = OpenAI(base_url=f"{OLLAMA_HOST.rstrip('/')}/v1", api_key="ollama")

    def run_turn(self, system_prompt, tools, tool_impl, conversation, max_turns):
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation:
            if "role" in turn and turn["role"] in ("user", "assistant", "tool", "system"):
                messages.append(turn)

        openai_tools = _to_openai_tools(tools) if tools else None
        tool_calls: list[ToolCallRecord] = []

        try:
            for _ in range(max_turns):
                response = self._client.chat.completions.create(
                    model=OLLAMA_MODEL,
                    messages=messages,
                    tools=openai_tools,
                )
                choice = response.choices[0]
                msg = choice.message
                messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

                if not msg.tool_calls:
                    return ProviderTurnResult(
                        reply=msg.content or "", tool_calls=tool_calls, raw_messages=messages
                    )

                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    output = _invoke(tool_impl, tc.function.name, args)
                    tool_calls.append(ToolCallRecord(name=tc.function.name, input=args, output=str(output)))
                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": str(output)}
                    )
        except Exception as e:  # noqa: BLE001
            return ProviderTurnResult(
                reply=(
                    f"[Could not reach Ollama at {OLLAMA_HOST}: {e}. "
                    "Is `ollama serve` running and is the model pulled "
                    f"(`ollama pull {OLLAMA_MODEL}`)?]"
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
