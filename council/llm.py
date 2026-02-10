"""LLM interaction layer supporting Ollama (local) and Anthropic (cloud)."""

from typing import Generator

from council.config import load_config


# ---------------------------------------------------------------------------
# Provider: Ollama
# ---------------------------------------------------------------------------

def _get_ollama_client():
    import ollama
    config = load_config()
    return ollama.Client(host=config.get("ollama_host", "http://localhost:11434"))


def _chat_ollama(
    messages: list[dict],
    system: str | None = None,
    model: str | None = None,
    stream: bool = True,
) -> Generator[str, None, None] | str:
    config = load_config()
    model = model or config.get("model", "qwen2.5:14b")

    if system:
        messages = [{"role": "system", "content": system}] + messages

    client = _get_ollama_client()

    if stream:
        response = client.chat(
            model=model,
            messages=messages,
            stream=True,
            options={
                "temperature": config.get("temperature", 0.7),
                "num_predict": config.get("max_tokens", 2048),
            },
        )
        for chunk in response:
            if chunk.get("message", {}).get("content"):
                yield chunk["message"]["content"]
    else:
        response = client.chat(
            model=model,
            messages=messages,
            stream=False,
            options={
                "temperature": config.get("temperature", 0.7),
                "num_predict": config.get("max_tokens", 2048),
            },
        )
        return response["message"]["content"]


def _check_ollama() -> tuple[bool, str]:
    try:
        client = _get_ollama_client()
        models = client.list()
        if not models.get("models"):
            return False, "No models available. Run 'ollama pull qwen2.5:14b' to get started."
        return True, "Ollama is ready"
    except Exception as e:
        return False, f"Cannot connect to Ollama: {e}. Make sure Ollama is running."


def _list_ollama_models() -> list[str]:
    try:
        client = _get_ollama_client()
        models = client.list()
        return [m["name"] for m in models.get("models", [])]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Provider: Anthropic
# ---------------------------------------------------------------------------

ANTHROPIC_MODELS = [
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-6",
]


def _get_anthropic_client():
    import anthropic
    config = load_config()
    api_key = config.get("anthropic_api_key", "")
    if not api_key:
        raise ValueError("Anthropic API key not configured. Set it in Settings.")
    return anthropic.Anthropic(api_key=api_key)


def _chat_anthropic(
    messages: list[dict],
    system: str | None = None,
    model: str | None = None,
    stream: bool = True,
) -> Generator[str, None, None] | str:
    config = load_config()
    model = model or config.get("anthropic_model", "claude-sonnet-4-5-20250929")

    # Anthropic uses a separate system parameter, not a system message in the list.
    # Filter out any system messages from the messages list.
    filtered = [m for m in messages if m.get("role") != "system"]

    client = _get_anthropic_client()

    kwargs = dict(
        model=model,
        max_tokens=config.get("max_tokens", 2048),
        messages=filtered,
    )
    if system:
        kwargs["system"] = system
    if config.get("temperature") is not None:
        kwargs["temperature"] = config.get("temperature", 0.7)

    if stream:
        with client.messages.stream(**kwargs) as stream_resp:
            for text in stream_resp.text_stream:
                yield text
    else:
        response = client.messages.create(**kwargs)
        return response.content[0].text


def _check_anthropic() -> tuple[bool, str]:
    config = load_config()
    api_key = config.get("anthropic_api_key", "")
    if not api_key:
        return False, "Anthropic API key not set. Add it in Settings."
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        # Quick validation: list models (lightweight call)
        client.models.list(limit=1)
        return True, "Anthropic API ready"
    except Exception as e:
        return False, f"Anthropic API error: {e}"


def _list_anthropic_models() -> list[str]:
    return list(ANTHROPIC_MODELS)


# ---------------------------------------------------------------------------
# Provider: OpenAI
# ---------------------------------------------------------------------------

OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "o3-mini",
]


def _get_openai_client():
    import openai
    config = load_config()
    api_key = config.get("openai_api_key", "")
    if not api_key:
        raise ValueError("OpenAI API key not configured. Set it in Settings.")
    return openai.OpenAI(api_key=api_key)


def _chat_openai(
    messages: list[dict],
    system: str | None = None,
    model: str | None = None,
    stream: bool = True,
) -> Generator[str, None, None] | str:
    config = load_config()
    model = model or config.get("openai_model", "gpt-4o")

    if system:
        messages = [{"role": "system", "content": system}] + messages

    client = _get_openai_client()

    kwargs = dict(
        model=model,
        messages=messages,
        max_tokens=config.get("max_tokens", 2048),
    )
    if config.get("temperature") is not None:
        kwargs["temperature"] = config.get("temperature", 0.7)

    if stream:
        response = client.chat.completions.create(stream=True, **kwargs)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    else:
        response = client.chat.completions.create(stream=False, **kwargs)
        return response.choices[0].message.content


def _check_openai() -> tuple[bool, str]:
    config = load_config()
    api_key = config.get("openai_api_key", "")
    if not api_key:
        return False, "OpenAI API key not set. Add it in Settings."
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        client.models.list()
        return True, "OpenAI API ready"
    except Exception as e:
        return False, f"OpenAI API error: {e}"


def _list_openai_models() -> list[str]:
    return list(OPENAI_MODELS)


# ---------------------------------------------------------------------------
# Provider: Google Gemini
# ---------------------------------------------------------------------------

GOOGLE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-pro-preview-05-06",
]


def _get_google_client():
    from google import genai
    config = load_config()
    api_key = config.get("google_api_key", "")
    if not api_key:
        raise ValueError("Google API key not configured. Set it in Settings.")
    return genai.Client(api_key=api_key)


def _chat_google(
    messages: list[dict],
    system: str | None = None,
    model: str | None = None,
    stream: bool = True,
) -> Generator[str, None, None] | str:
    from google.genai import types

    config = load_config()
    model = model or config.get("google_model", "gemini-2.0-flash")

    # Convert messages to Gemini format
    contents = []
    for m in messages:
        role = m.get("role", "user")
        if role == "system":
            continue  # handled via system_instruction
        gemini_role = "model" if role == "assistant" else "user"
        contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=m["content"])],
            )
        )

    gen_config = types.GenerateContentConfig(
        max_output_tokens=config.get("max_tokens", 2048),
    )
    if config.get("temperature") is not None:
        gen_config.temperature = config.get("temperature", 0.7)
    if system:
        gen_config.system_instruction = system

    client = _get_google_client()

    if stream:
        response = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=gen_config,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    else:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=gen_config,
        )
        return response.text


def _check_google() -> tuple[bool, str]:
    config = load_config()
    api_key = config.get("google_api_key", "")
    if not api_key:
        return False, "Google API key not set. Add it in Settings."
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        # Quick validation: list models
        list(client.models.list(config={"page_size": 1}))
        return True, "Google Gemini API ready"
    except Exception as e:
        return False, f"Google Gemini API error: {e}"


def _list_google_models() -> list[str]:
    return list(GOOGLE_MODELS)


# ---------------------------------------------------------------------------
# Public API — routes to the active provider
# ---------------------------------------------------------------------------

_CHAT_DISPATCH = {
    "anthropic": _chat_anthropic,
    "openai": _chat_openai,
    "google": _chat_google,
}

_CHECK_DISPATCH = {
    "anthropic": _check_anthropic,
    "openai": _check_openai,
    "google": _check_google,
}

_LIST_DISPATCH = {
    "anthropic": _list_anthropic_models,
    "openai": _list_openai_models,
    "google": _list_google_models,
}


def _get_provider() -> str:
    config = load_config()
    return config.get("provider", "ollama")


def chat(
    messages: list[dict],
    system: str | None = None,
    model: str | None = None,
    stream: bool = True,
) -> Generator[str, None, None] | str:
    """
    Send a chat request to the configured LLM provider.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system: System prompt to prepend
        model: Model to use (defaults to config)
        stream: Whether to stream the response

    Yields/Returns:
        Response chunks if streaming, full response if not
    """
    provider = _get_provider()
    fn = _CHAT_DISPATCH.get(provider, _chat_ollama)
    return fn(messages, system, model, stream)


def check_ollama_available() -> tuple[bool, str]:
    """Check if the configured LLM provider is available."""
    provider = _get_provider()
    fn = _CHECK_DISPATCH.get(provider, _check_ollama)
    return fn()


def list_available_models() -> list[str]:
    """List available models for the configured provider."""
    provider = _get_provider()
    fn = _LIST_DISPATCH.get(provider, _list_ollama_models)
    return fn()
