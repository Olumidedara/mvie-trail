import json

from ..config import env


def groq_client():
    key = env("GROQ_API_KEY", "")
    if not key:
        return None
    try:
        from openai import OpenAI

        return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)
    except Exception:
        return None


def transcribe(client, audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
    return result.text or ""


def chat_json(client, model: str, system: str, user: str, temperature: float = 0.7) -> dict:
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