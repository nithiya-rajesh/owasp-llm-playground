import os

# Which backend to use: "anthropic" | "gemini" | "ollama"
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "anthropic").strip().lower()

MAX_TOOL_TURNS = int(os.environ.get("PLAYGROUND_MAX_TOOL_TURNS", "10"))

# --- Anthropic ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# --- Gemini (free tier friendly) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# "gemini-flash-latest" is Google's own rolling alias — it auto-updates to
# whatever the current stable Flash model is, so this default doesn't go
# stale the way a pinned version string (e.g. "gemini-2.5-flash") eventually
# will when Google retires that specific model for new users. Pin an exact
# version yourself via GEMINI_MODEL if you want reproducible behavior
# instead of auto-updates.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

# --- Ollama (fully local, no API key) ---
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")


def describe_active_provider() -> str:
    if MODEL_PROVIDER == "anthropic":
        return f"Anthropic ({ANTHROPIC_MODEL})"
    if MODEL_PROVIDER == "gemini":
        return f"Gemini ({GEMINI_MODEL})"
    if MODEL_PROVIDER == "ollama":
        return f"Ollama ({OLLAMA_MODEL} @ {OLLAMA_HOST})"
    return f"Unknown provider '{MODEL_PROVIDER}'"


def _warn_if_misconfigured():
    if MODEL_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        print(
            "[WARNING] MODEL_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
        )
    elif MODEL_PROVIDER == "gemini" and not GEMINI_API_KEY:
        print(
            "[WARNING] MODEL_PROVIDER=gemini but GEMINI_API_KEY is not set.\n"
            "  Get a free key at https://aistudio.google.com/apikey and:\n"
            "  export GEMINI_API_KEY=...\n"
        )
    elif MODEL_PROVIDER not in ("anthropic", "gemini", "ollama"):
        print(
            f"[WARNING] Unknown MODEL_PROVIDER '{MODEL_PROVIDER}'. "
            "Expected one of: anthropic, gemini, ollama."
        )


_warn_if_misconfigured()
