import json

from ..models import Narrative, Scene
from . import groq

SCRIPT_SYSTEM = (
    "You write dramatic, cinematic storytelling narration for short social videos "
    "built from public-domain and stock footage. Return JSON only with keys: "
    'title, description, tags (list of 6), hook (one strong opening line), '
    "scenes (list of objects with keys query, visual_hint, text). "
    "The text field is the voiceover line for that scene. Keep the total voiceover "
    "length near the target duration, roughly 2.4 words per second spoken."
)

FALLBACK_DATA = {
    "vintage science fiction": {
        "queries": ["vintage electronics", "night sky stars", "desert road", "space satellite", "old laboratory", "rocket launch"],
        "hints": ["glowing retro machinery", "endless starfield", "lonely highway at night", "orbiting machine", "arcane lab instruments", "thunderous ascent"],
    },
    "film noir": {
        "queries": ["rainy city street", "old typewriter", "dark alley", "smoke", "phone booth", "city skyline night"],
        "hints": ["neon reflections on wet asphalt", "dusty keys clacking", "shadows and fog", "silent curls of smoke", "a ringing phone", "skyline fading into dark"],
    },
    "horror": {
        "queries": ["dark forest", "old house", "fog", "candles", "crows", "empty corridor"],
        "hints": ["trees bending in the wind", "a creaking gate", "slow rolling mist", "flickering candlelight", "birds scattering", "long shadows ahead"],
    },
}


def build_narrative(cfg: dict, analysis: dict, genre: str, count: int, log) -> Narrative:
    total = int(cfg["script"].get("total_duration_s", 60))
    scenes_count = int(cfg["script"].get("scene_count", 6))
    words_per_scene = max(6, int((total / scenes_count) * 2.4))
    client = groq.groq_client()
    if client:
        try:
            payload = groq.chat_json(
                client,
                cfg["script"]["model"],
                SCRIPT_SYSTEM,
                json.dumps(
                    {
                        "genre": genre,
                        "mood": analysis.get("mood", []),
                        "themes": analysis.get("themes", []),
                        "keywords": analysis.get("keywords", []),
                        "pitch": analysis.get("pitch", ""),
                        "target_duration_seconds": total,
                        "scene_count": scenes_count,
                        "words_per_scene": words_per_scene,
                    }
                ),
                temperature=0.8,
            )
            narrative = _from_payload(payload, count)
            if len(narrative.scenes) >= 3:
                return narrative
        except Exception as exc:
            log(f"script LLM failed, using fallback: {exc}")
    return _fallback(cfg, genre, count)


def _from_payload(payload: dict, count: int) -> Narrative:
    scenes = []
    for i, s in enumerate(payload.get("scenes", [])):
        scenes.append(
            Scene(
                index=i,
                query=str(s.get("query", "")).strip(),
                text=str(s.get("text", "")).strip(),
                visual_hint=str(s.get("visual_hint", "")).strip(),
            )
        )
    narrative = Narrative(
        title=str(payload.get("title", "")).strip(),
        description=str(payload.get("description", "")).strip(),
        tags=[str(t) for t in payload.get("tags", [])][:6],
        hook=str(payload.get("hook", "")).strip(),
        scenes=scenes,
    )
    return narrative


def _fallback(cfg: dict, genre: str, count: int) -> Narrative:
    entries = FALLBACK_DATA.get(genre.lower(), FALLBACK_DATA["vintage science fiction"])
    scenes = []
    lines = [
        "nothing about this place is what it seems.",
        "they said it could not be done.",
        "but someone, somewhere, was listening.",
        "when the signal finally came, it changed everything.",
        "there is no turning back now.",
        "and in the silence, a story begins to rise.",
    ]
    for i, (q, hint, line) in enumerate(zip(entries["queries"], entries["hints"], lines)):
        scenes.append(Scene(index=i, query=q, visual_hint=hint, text=line))
    kw = ", ".join(entries["queries"][:3])
    return Narrative(
        title=f"The Signal from {genre.title()}",
        description=f"A cinematic storytelling short inspired by {genre} footage.",
        tags=[genre, "shortfilm", "cinematic", "story", "viral", "film"],
        hook="some stories are never meant to be told... until now.",
        scenes=scenes,
    )