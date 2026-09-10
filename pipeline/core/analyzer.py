from ..models import SourceClip
from . import groq, media

ANALYSIS_SYSTEM = (
    "You are a film analyst. Given a transcript and a genre, return JSON with keys: "
    '"mood" (list of words), "themes" (list), "keywords" (list of 8 searchable terms), '
    '"pitch" (one sentence describing the story being told).'
)


def analyze(cfg: dict, clip: SourceClip, log) -> dict:
    base = {
        "mood": ["cinematic", "dramatic"],
        "themes": ["mystery", "adventure"],
        "keywords": [cfg["source"]["genres"][0]],
        "pitch": "A forgotten story resurfacing from the archives.",
        "transcript": "",
    }
    transcript = ""
    if not clip.local_path:
        return base
    try:
        ext = clip.local_path.rsplit(".", 1)[-1]
        wav = f"{clip.local_path}.wav"
        media.run([media.ffmpeg(), "-y", "-i", clip.local_path, "-ar", "16000", "-ac", "1", wav]).check_returncode()
        client = groq.groq_client()
        if client:
            transcript = groq.transcribe(client, wav) or ""
    except Exception as exc:
        log(f"analysis transcription failed: {exc}")
        transcript = ""
    base["transcript"] = transcript
    if not transcript.strip():
        return base
    try:
        client = groq.groq_client()
        if not client:
            return base
        summary = groq.chat_json(
            client,
            cfg["script"]["model"],
            ANALYSIS_SYSTEM,
            f'Genre: {", ".join(cfg["source"]["genres"])}.\nTranscript:\n{transcript[:4000]}',
            temperature=0.4,
        )
        for k in ("mood", "themes", "keywords", "pitch"):
            if k in summary:
                base[k] = summary[k]
    except Exception as exc:
        log(f"analysis LLM failed: {exc}")
    return base