# Project Overview — Current State & Planned Multi-Provider Build

This document explains, precisely, how the app works today and what's about
to change. Read this before the build starts so the plan makes sense in
context, not just as a diff.

---

## Part 1: How the app works right now

### The request flow, end to end

```
Browser (static HTML/JS)
   │
   │  POST /api/chat  { session_id, scenario_id, message }
   ▼
FastAPI (app/main.py)
   │
   │  1. look up the Scenario object by scenario_id (app/scenarios/__init__.py)
   │  2. pull the session's conversation history (app/core/state.py, in-memory)
   │  3. get/create that scenario's mutable "fake server-side data" dict
   ▼
app/core/agent.py :: run_agent_turn()
   │
   │  Builds ONE request to Anthropic's Messages API:
   │    - system = scenario.system_prompt
   │    - tools  = scenario.tools (JSON schema)
   │    - messages = full conversation so far
   ▼
Anthropic API (api.anthropic.com)
   │
   │  Claude either:
   │    (a) replies with text directly → loop ends, return to browser, OR
   │    (b) replies with a tool_use block → we run scenario's own tool_impl
   │        function (the vulnerable behavior lives here), get an output
   │        string, and send it BACK to the API as a tool_result → repeat
   ▼
(repeats up to MAX_TOOL_TURNS times per single user message)
   │
   ▼
FastAPI returns { reply, tool_calls[], flag }
   │
   ▼
Browser renders the reply, the tool-call log, and (if scenario.check_flag()
fired) the 🚩 banner.
```

### Where the "vulnerability" actually lives

Every scenario's danger is **in the tool implementation Python code**, not in
the LLM. For example, LLM01's `search_documents()` just concatenates file
contents into a string with no delimiters — the model isn't "hacked," it's
simply given untrusted text with no signal that it's untrusted, exactly like
a real RAG pipeline that skips sanitization. This is why the exploit
detection (`check_flag`) can be deterministic Python — it's checking
*"did the vulnerable code path get triggered,"* not judging the model.

### Where the API call happens, and why it costs money

`run_agent_turn()` in `app/core/agent.py` is the **only** place that talks
to a model provider. Right now that's hardcoded to:

```python
from anthropic import Anthropic
_client = Anthropic(api_key=ANTHROPIC_API_KEY)
...
_client.messages.create(model=MODEL, max_tokens=1024, system=..., tools=..., messages=...)
```

Each call to `.messages.create()` is billed by the provider per token (input
+ output). One user message can trigger **multiple** calls in the tool-use
loop (see the "repeats" arrow above) — so cost scales with how many tool
hops a given exploit needs, not with whether you succeed or fail, and not
per-flag. Failing an attempt 5 times costs roughly 5x a single clean success.

### What's hardcoded today (the actual limitation)

| Thing | Current reality |
|---|---|
| Model provider | Anthropic only, via the `anthropic` SDK |
| Model string | `claude-sonnet-4-6` (stale — needs updating to `claude-sonnet-5`) |
| Tool-call format | Anthropic's `tool_use` / `tool_result` block shape, baked into `agent.py` and every `scenario.py`'s `tools` list |
| Config | One env var: `ANTHROPIC_API_KEY` |
| Cost to a contributor | Whatever their Anthropic key bills them — no free path today |

---

## Part 2: What's changing — multi-provider support

### Goal

Anyone cloning the repo can choose **any** of:
1. **Anthropic** (Claude) — if they already have a key
2. **Google Gemini** — genuinely free tier, no credit card, this becomes the
   default recommended path for the open-source audience
3. **Local / Ollama** — completely free forever, runs on their own machine,
   no API key at all, for people who want zero ongoing dependency on any
   vendor

### The core design problem to solve

Each provider's API has a **different shape** for the exact same concept
(tool calling):

| Concept | Anthropic | Gemini | OpenAI-compatible (Ollama) |
|---|---|---|---|
| SDK | `anthropic` | `google-genai` | `openai` (Ollama exposes an OpenAI-compatible endpoint) |
| Tool result marker | `stop_reason == "tool_use"` | `function_call` parts | `finish_reason == "tool_calls"` |
| Tool definition schema | `input_schema` (JSON Schema) | `parameters` (JSON Schema, slightly different wrapper) | `parameters` (JSON Schema, OpenAI function-call wrapper) |
| Returning a tool result | `tool_result` content block | `function_response` part | `role: "tool"` message |

**The fix:** introduce one internal, provider-agnostic shape that
`app/main.py` and every `scenario.py` already speak (a plain Python dict:
`{name, input}` for a tool call, and `{name, output}` for a result — this is
*already* what `ToolCallRecord` looks like today). Then write one small
adapter per provider that translates:

```
scenario.tools (our shape) → provider's tool schema     [outbound]
provider's response        → our ToolCallRecord shape   [inbound]
```

This means **zero changes to any of the 10 scenario files** — they already
only deal with our internal shape. All the new work is contained to
`app/core/`.

### Planned file changes

```
app/core/
  agent.py            # becomes provider-agnostic dispatcher (thin)
  providers/
    __init__.py       # get_provider(name) -> provider instance
    base.py           # Provider protocol: run_turn(system, tools, messages) -> AgentTurnResult
    anthropic_provider.py   # today's logic, moved here, model string fixed
    gemini_provider.py      # new
    ollama_provider.py      # new (talks to local Ollama's OpenAI-compatible endpoint)
  config.py           # adds MODEL_PROVIDER env var + per-provider settings
```

### Config changes (`.env`)

```bash
# Pick one:
MODEL_PROVIDER=anthropic        # or: gemini | ollama

# Anthropic (only needed if MODEL_PROVIDER=anthropic)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5

# Gemini (only needed if MODEL_PROVIDER=gemini) — recommended free path
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash

# Ollama (only needed if MODEL_PROVIDER=ollama) — fully local, no key
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

### UI change

A small read-only badge in the header ("Running on: Gemini 2.5 Flash") so
whoever's testing knows which backend is live — no dropdown needed in v1
since it's an env-level choice, not per-session.

### What does NOT change

- All 10 scenario files — untouched, since they only speak the internal
  shape.
- The flag-detection logic — untouched, it inspects `ToolCallRecord` objects
  and reply text, same as today.
- The frontend chat UI — untouched except the small provider badge.
- Docker setup — just gains the new env vars in `docker-compose.yml`.

### Caveat worth knowing before we build

Smaller/local models (via Ollama) are **less reliable at reliably following
tool-calling instructions** than Claude or Gemini — some scenarios (LLM01's
injection chain especially) may need a couple of extra nudges or may behave
inconsistently on a small local model. That's a real, worth-documenting
limitation, not a bug — I'll note it plainly in the README rather than
overselling the local option as a perfect substitute.

### Build order I'd suggest

1. `providers/base.py` — define the common interface
2. `providers/anthropic_provider.py` — move existing logic, fix the model
   string
3. `providers/gemini_provider.py` — new, since it's the free-tier priority
4. `providers/ollama_provider.py` — new
5. `config.py` + `.env.example` updates
6. Update `agent.py` to dispatch to the selected provider
7. Small UI badge
8. Re-run the full exploit-logic test suite (`tests/test_exploit_logic.py`)
   against all three providers to confirm nothing regressed
9. Update README + TESTING_GUIDE with the three setup paths, Gemini as the
   headline free option

---

## Quick summary if you just want the TL;DR

- **Today:** one file (`agent.py`) hardcodes a call to Anthropic's API; every
  scenario is provider-agnostic already and won't need to change.
- **Cost today:** per-token, per-API-call, multiplied by however many tool
  hops one exploit needs — not per flag.
- **Plan:** add a thin `providers/` layer so `MODEL_PROVIDER` in `.env`
  switches between Anthropic, Gemini (free), or local Ollama (free), with
  no changes needed to any of the 10 scenarios.

Let me know if you want any part of this plan adjusted before I start
building — e.g. adding OpenAI as a fourth provider, or making the provider
selectable per-session in the UI instead of env-level.
