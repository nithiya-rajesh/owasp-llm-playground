# OWASP LLM Top 10 Playground

[![CI](https://github.com/nithiya-rajesh/owasp-llm-playground/actions/workflows/ci.yml/badge.svg)](https://github.com/nithiya-rajesh/owasp-llm-playground/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Free, open-source, hands-on practice for the OWASP Top 10 for LLM
Applications — no paid subscription required.** Runs entirely on your own
machine, and works with a free Gemini API key or a fully offline local
model (Ollama) — an Anthropic key is optional, not required.

A deliberately vulnerable AI agent application for hands-on practice against
the **[OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/)**.
Think "WebGoat / DVWA / Juice Shop," but for LLM and agentic AI security.

Twenty-five self-contained scenarios — spanning direct exploits, indirect/
multi-turn attacks, and multi-agent trust failures — each with a
working (and exploitable) tool-calling agent, an in-app objective/hints/fix
guide, and a CTF-style flag you capture on successful exploitation.

**Run it only on your own machine, against your own local instance. This app
is intentionally insecure — never deploy it publicly or point it at real
credentials, data, or production services.**

## Features

- 🎯 **25 self-contained scenarios** — covering direct exploits, indirect/multi-turn attacks, and multi-agent trust failures across all 10 OWASP LLM Top 10:2025 categories
- 🧩 **Self-discovering architecture** — drop a new folder in `app/scenarios/`, it's picked up automatically, zero registry edits
- 🔌 **Three interchangeable model backends** — Anthropic, Google Gemini (free tier), or fully offline Ollama, switchable with one env var
- 🏁 **CTF-style flag capture** — deterministic, server-side exploit detection; no guessing whether you "really" succeeded
- 📖 **In-app training material** — Objective, Hints, and a Fix/remediation guide (mapped to real-world root causes) for every scenario
- 🔍 **Full transparency by design** — a live tool-call log shows exactly what the agent did, so you can see an exploit land in real time
- 🐳 **One-command Docker setup** — `docker compose up --build` and you're running, including a bundled local-inference option
- ✅ **CI-verified** — every scenario's exploit path is checked by an automated test suite on every push

## Table of Contents

- [Scenarios](#scenarios)
- [Choosing a backend](#choosing-a-backend)
- [Quick start (without Docker)](#quick-start-without-docker)
- [How it works](#how-it-works)
- [Adding a new scenario](#adding-a-new-scenario)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)
- [Project History](#project-history)
- [License](#license)

## Scenarios

**25 scenarios**, grouped by OWASP category — most categories have two or
three distinct attack mechanisms to practice against, from straightforward
single-agent exploits through to multi-agent trust failures.

| OWASP ID | Category | Scenarios in this category |
|----------|----------|------------------------------|
| LLM01:2025 | Prompt Injection | Indirect injection via a poisoned RAG document · Multi-turn memory injection · Cross-agent injection propagation |
| LLM02:2025 | Sensitive Information Disclosure | Over-shared tool output & a secret in the system prompt · Error-message data disclosure · Cross-agent data leakage |
| LLM03:2025 | Supply Chain | Typosquatted plugin metadata · Malicious model adapter backdoor · Compromised sub-agent registry |
| LLM04:2025 | Data and Model Poisoning | Poisoned feedback loop · Few-shot example poisoning |
| LLM05:2025 | Improper Output Handling | Stored XSS via unsanitized HTML · Agent-driven SSRF |
| LLM06:2025 | Excessive Agency | Unconfirmed financial transfer · Unscoped admin tool abuse · Orchestrator blind trust |
| LLM07:2025 | System Prompt Leakage | Direct/reframed extraction · Diagnostic error-channel leakage |
| LLM08:2025 | Vector and Embedding Weaknesses | No tenant isolation · Adversarial ranking manipulation · Shared memory poisoning |
| LLM09:2025 | Misinformation | Confident fabrication under pressure · Citation hallucination |
| LLM10:2025 | Unbounded Consumption | Runaway pagination loop · Recursive sub-agent delegation |

See `docs/OWASP_MAPPING.md` for the full breakdown of every scenario's
exact mechanism and fix.

## Choosing a backend

This app supports three interchangeable model providers, switched with one
env var (`MODEL_PROVIDER`). Pick whichever fits your situation:

| Provider | Cost | Setup effort | Notes |
|---|---|---|---|
| **Gemini** *(recommended if you don't already have a key)* | Free, no credit card | Lowest — sign up, get a key | Genuine free tier; best default for the "no paid subscription" audience |
| **Ollama** | Free forever, fully offline | Medium — install Ollama, pull a model | No API key, no internet needed after setup; see hardware notes below |
| **Anthropic** | Paid, usage-based | Lowest if you already have a key | Best tool-calling reliability of the three |

### Option A — Gemini (recommended free path)

```bash
git clone <your-fork-url>
cd owasp-llm-playground
cp .env.example .env
# edit .env: MODEL_PROVIDER=gemini, GEMINI_API_KEY=<free key from https://aistudio.google.com/apikey>
docker compose up --build
```

### Option B — Ollama (fully local, zero cost forever)

```bash
git clone <your-fork-url>
cd owasp-llm-playground
cp .env.example .env
# edit .env: MODEL_PROVIDER=ollama
docker compose up --build
# in a separate terminal, once containers are up:
docker compose exec ollama ollama pull llama3.1
```

**Hardware guidance for local models:**

| Tier | Example model | RAM needed | Reliability |
|---|---|---|---|
| Fast/small | `llama3.2:3b`, `gemma2:2b` | ~4-6GB free | Runs on almost any laptop, but noticeably less reliable at multi-step tool-calling scenarios (LLM01, LLM03, LLM06) — some flags may not trigger consistently |
| Recommended mid-size | `llama3.1:8b`, `qwen2.5:7b` | ~8-10GB free (16GB system RAM recommended) | Solid tool-calling support, closer to what Claude/Gemini demonstrate |

Change the model with `OLLAMA_MODEL=llama3.1` (or any tag from
[ollama.com/library](https://ollama.com/library)) in your `.env`, then
`docker compose exec ollama ollama pull <model>`.

**This app is designed for single-user, local use** — the in-memory session
store and (if using Ollama) the local inference engine are not built for
concurrent multi-user production traffic. That's fine for a training tool
run on your own machine; don't deploy this as a shared public service.

### Option C — Anthropic (if you already have a key)

```bash
git clone <your-fork-url>
cd owasp-llm-playground
cp .env.example .env
# edit .env: MODEL_PROVIDER=anthropic, ANTHROPIC_API_KEY=sk-ant-...
docker compose up --build
```

Open **http://localhost:8000** for any of the above. A badge in the sidebar
confirms which backend is active.

## Quick start (without Docker)

```bash
git clone <your-fork-url>
cd owasp-llm-playground
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export MODEL_PROVIDER=gemini   # or anthropic / ollama
export GEMINI_API_KEY=your-free-key-here
uvicorn app.main:app --reload
```

Open **http://localhost:8000**.

## How it works

- Pick a scenario from the sidebar. Each one spins up a small, purpose-built
  agent with its own system prompt and tools.
- Chat with it in the main panel. The **Tool calls** tab shows exactly what
  the agent called and what it got back — this transparency is intentional;
  a real production app would never expose this much, but seeing it is how
  you learn to recognize an exploit succeeding.
- Read the **Objective** tab for the goal, and **Hints** if you get stuck.
- Once you trigger the vulnerability, a flag is captured automatically and
  the **Fix** tab unlocks with the remediation guidance.
- **Reset session** clears the conversation and any scenario state so you
  can retry from scratch.

## Adding a new scenario

Scenarios are self-discovering. To add one:

1. Create `app/scenarios/<your_id>/scenario.py` exporting a `SCENARIO =
   Scenario(...)` instance (see `app/scenarios/base.py` for the dataclass
   fields, and any existing scenario for a working example).
2. Add any supporting files (e.g. `docs/` for RAG-style content) alongside it.
3. Restart the app — it's picked up automatically, no registry edits needed.

See `CONTRIBUTING.md` for style guidelines and PR expectations.

## Architecture

```
app/
  core/
    agent.py            # thin, provider-agnostic dispatcher
    agent_types.py       # shared ToolCallRecord / AgentTurnResult shapes
    config.py            # env var config, MODEL_PROVIDER switch
    state.py             # in-memory per-session state (single-user, local only)
    providers/
      base.py             # Provider interface every backend implements
      anthropic_provider.py
      gemini_provider.py
      ollama_provider.py
  scenarios/
    base.py        # Scenario dataclass every module implements
    llm01_prompt_injection/
      scenario.py
      docs/        # poisoned + benign "knowledge base" documents
    llm02_sensitive_info_disclosure/
    ...
  static/          # vanilla HTML/CSS/JS frontend (no build step)
  main.py          # FastAPI app: /api/scenarios, /api/chat, /api/reset, /api/provider
```

Scenario files never talk to a provider directly — they only see the neutral
`ToolCallRecord`/`AgentTurnResult` shapes, so switching `MODEL_PROVIDER`
requires zero changes to any of the 10 scenarios.

No database, no auth, no persistence beyond process memory — this is a
training tool, not a template for production architecture. Do not reuse the
security patterns you see here in anything real; that's the whole point.

## Requirements

- Python 3.11+ (if running without Docker)
- One of: a free [Gemini API key](https://aistudio.google.com/apikey)
  (recommended), a local [Ollama](https://ollama.com) install, or an
  [Anthropic API key](https://console.anthropic.com/)
- Docker + Docker Compose (optional, recommended)

## Troubleshooting

**Ollama never responds / hangs indefinitely, no error at all**

Check `docker compose logs ollama` for a line like:
```
inference compute ... total="3.5 GiB" available="3.4 GiB"
```
If the model you're trying to run needs more memory than Docker has
available (an 8B model needs roughly 4.5-5GB just to load), it will hang
trying to load rather than fail cleanly — this looks identical to "just
slow" but never actually resolves. Fix: either switch to a smaller model
(`OLLAMA_MODEL=llama3.2:3b` needs ~2GB) or increase Docker Desktop's memory
allocation (Settings → Resources → Memory) if your host machine has the
RAM to spare, then restart Docker.

**Provider badge shows the wrong backend after changing `.env`**

`docker compose up` alone won't always pick up changes if an image was
cached. Force it: `docker compose down && docker compose build --no-cache && docker compose up`.

**"Unexpected token... is not valid JSON" in the chat**

This means an unhandled server error occurred and returned a non-JSON
error page instead of the expected response. Check `docker compose logs
app` for the actual traceback — if you don't see a bracketed `[...]` error
message in the chat itself, you may be running an older build; re-pull/
re-extract the project and rebuild with `--no-cache`.

## Project History

This started as a 10-scenario v1 (one mechanism per OWASP category), then
grew in two rounds of development:

- **Round 2** added a second, genuinely different attack mechanism to every
  category — e.g. Prompt Injection went from "indirect injection via a
  poisoned document" to also covering "multi-turn injection via planted
  memory," not just a rephrased version of the same attack.
- **Round 3** added multi-agent scenarios — attacks that only make sense
  once you have two or more agents trusting each other's output, like a
  compromised sub-agent or a poisoned shared memory store, which is a
  meaningfully different architecture from a single agent with tools.

All of that is merged into the single, current codebase you're looking at
— there's nothing separate to install or switch between; every scenario
described above is active in this one app. Older tagged releases (if
you're browsing GitHub releases/tags) reflect earlier snapshots of this
same history.

## License

MIT — see `LICENSE`. Contributions welcome; see `CONTRIBUTING.md` and our
`CODE_OF_CONDUCT.md`.
