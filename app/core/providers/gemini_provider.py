"""
Gemini function-calling notes (google-genai SDK):
  - Tool schema uses `parameters` instead of Anthropic's `input_schema`,
    wrapped in a FunctionDeclaration.
  - The model's turn is a list of `parts`; a tool call arrives as a
    `function_call` part (name + args dict), not a top-level stop_reason.
  - We send a tool result back as a `function_response` part in a new
    "user"-role (actually "function"/"tool" role, SDK-dependent) turn.

This adapter keeps all of that translation local to this file — the rest of
the app never sees Gemini's shapes.
"""

from app.core.providers.base import Provider, ProviderTurnResult
from app.core.agent_types import ToolCallRecord
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL


def _to_gemini_tools(tools: list[dict]):
    from google.genai import types

    declarations = []
    for t in tools:
        declarations.append(
            types.FunctionDeclaration(
                name=t["name"],
                description=t.get("description", ""),
                parameters=t.get("input_schema", {"type": "object", "properties": {}}),
            )
        )
    return [types.Tool(function_declarations=declarations)] if declarations else None


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self):
        self._client = None
        if GEMINI_API_KEY:
            from google import genai
            self._client = genai.Client(api_key=GEMINI_API_KEY)

    def run_turn(self, system_prompt, tools, tool_impl, conversation, max_turns):
        if self._client is None:
            return ProviderTurnResult(
                reply=(
                    "[Server misconfigured: GEMINI_API_KEY is not set. Get a free key at "
                    "https://aistudio.google.com/apikey and export GEMINI_API_KEY=...]"
                ),
                tool_calls=[],
                raw_messages=conversation,
            )

        from google.genai import types

        # conversation entries are either our neutral {"role","content"} shape
        # (plain user/assistant text turns) or already-native Gemini Content
        # objects appended by a previous call to this same provider.
        history = []
        for turn in conversation:
            if isinstance(turn, types.Content):
                history.append(turn)
            else:
                role = "user" if turn["role"] == "user" else "model"
                history.append(types.Content(role=role, parts=[types.Part(text=str(turn["content"]))]))

        gemini_tools = _to_gemini_tools(tools)
        config = types.GenerateContentConfig(system_instruction=system_prompt, tools=gemini_tools)

        tool_calls: list[ToolCallRecord] = []

        try:
            for _ in range(max_turns):
                response = self._client.models.generate_content(
                    model=GEMINI_MODEL, contents=history, config=config
                )
                candidate = response.candidates[0]
                history.append(candidate.content)

                function_calls = [p.function_call for p in candidate.content.parts if p.function_call]
                if not function_calls:
                    text = "".join(p.text for p in candidate.content.parts if p.text)
                    return ProviderTurnResult(reply=text, tool_calls=tool_calls, raw_messages=history)

                response_parts = []
                for fc in function_calls:
                    args = dict(fc.args) if fc.args else {}
                    output = _invoke(tool_impl, fc.name, args)
                    tool_calls.append(ToolCallRecord(name=fc.name, input=args, output=str(output)))
                    response_parts.append(
                        types.Part.from_function_response(name=fc.name, response={"result": str(output)})
                    )
                history.append(types.Content(role="user", parts=response_parts))
        except Exception as e:  # noqa: BLE001
            return ProviderTurnResult(
                reply=(
                    f"[Gemini API error: {e}. Check that GEMINI_API_KEY in your .env "
                    "is a real, valid key and that you haven't hit the free-tier rate "
                    "limit (wait a minute and retry).]"
                ),
                tool_calls=tool_calls,
                raw_messages=history,
            )

        return ProviderTurnResult(
            reply="[Max tool-call turns reached for this message.]",
            tool_calls=tool_calls,
            raw_messages=history,
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
