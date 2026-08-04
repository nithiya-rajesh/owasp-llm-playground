from app.core.config import MODEL_PROVIDER

_instance = None


def get_provider():
    global _instance
    if _instance is not None:
        return _instance

    if MODEL_PROVIDER == "anthropic":
        from app.core.providers.anthropic_provider import AnthropicProvider
        _instance = AnthropicProvider()
    elif MODEL_PROVIDER == "gemini":
        from app.core.providers.gemini_provider import GeminiProvider
        _instance = GeminiProvider()
    elif MODEL_PROVIDER == "ollama":
        from app.core.providers.ollama_provider import OllamaProvider
        _instance = OllamaProvider()
    else:
        raise ValueError(
            f"Unknown MODEL_PROVIDER '{MODEL_PROVIDER}'. Expected: anthropic, gemini, ollama."
        )
    return _instance
