import json

from ..config import env

CHAT_MODEL_CANDIDATES = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "groq/compound",
    "groq/compound-mini",
)

_models_cache: list[str] = []


def groq_client():
    key = env("GROQ_API_KEY", "")
    if not key:
        return None
    try:
        from openai import OpenAI

        return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)
    except Exception:
        return None


def available_models(client) -> list[str]:
    global _models_cache
    if _models_cache:
        return _models_cache
    try:
        _models_cache = [m.id for m in client.models.list().data]
    except Exception:
        _models_cache = []
    return _models_cache


def resolve_chat_model(client, preferred: str) -> str:
    ids = available_models(client)
    if preferred and preferred in ids:
        return preferred
    for candidate in CHAT_MODEL_CANDIDATES:
        if candidate in ids:
            return candidate
    return preferred


def transcribe(client, audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
    return result.text or ""


def chat_json(client, preferred: str, system: str, user: str, temperature: float = 0.7) -> dict:
    model = resolve_chat_model(client, preferred)
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)