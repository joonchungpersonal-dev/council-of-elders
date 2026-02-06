"""LLM interaction layer using Ollama."""

from typing import Generator

import ollama

from council.config import load_config


def get_client() -> ollama.Client:
    """Get an Ollama client."""
    config = load_config()
    return ollama.Client(host=config.get("ollama_host", "http://localhost:11434"))


def chat(
    messages: list[dict],
    system: str | None = None,
    model: str | None = None,
    stream: bool = True,
) -> Generator[str, None, None] | str:
    """
    Send a chat request to Ollama.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system: System prompt to prepend
        model: Model to use (defaults to config)
        stream: Whether to stream the response

    Yields/Returns:
        Response chunks if streaming, full response if not
    """
    config = load_config()
    model = model or config.get("model", "qwen2.5:14b")

    # Prepend system message if provided
    if system:
        messages = [{"role": "system", "content": system}] + messages

    client = get_client()

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


def check_ollama_available() -> tuple[bool, str]:
    """Check if Ollama is available and a model is loaded."""
    try:
        client = get_client()
        models = client.list()
        if not models.get("models"):
            return False, "No models available. Run 'ollama pull qwen2.5:14b' to get started."
        return True, "Ollama is ready"
    except Exception as e:
        return False, f"Cannot connect to Ollama: {e}. Make sure Ollama is running."


def list_available_models() -> list[str]:
    """List available Ollama models."""
    try:
        client = get_client()
        models = client.list()
        return [m["name"] for m in models.get("models", [])]
    except Exception:
        return []
