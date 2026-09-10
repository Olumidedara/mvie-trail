import asyncio
import os

import edge_tts

from ..models import Narrative
from . import media

GAP_S = 0.18


async def _synth(text: str, voice: str, rate: str, volume: str, out: str) -> None:
    comm = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await comm.save(out)


def generate(cfg: dict, narrative: Narrative, workdir: str, log) -> str:
    voice = cfg["voiceover"].get("voice", "en-US-GuyNeural")
    rate = cfg["voiceover"].get("rate", "+0%")
    volume = cfg["voiceover"].get("volume", "+0%")
    items: list[str] = []
    start = 0.0
    for scene in narrative.scenes:
        out = os.path.join(workdir, f"vo_{scene.index}.mp3")
        asyncio.run(_synth(scene.text, voice, rate, volume, out))
        duration = media.probe(out).get("duration", 4.0) or 4.0
        scene.audio_path = out
        scene.duration = duration
        scene.start = start
        start += duration + GAP_S
        items.append(out)
        silence = os.path.join(workdir, f"gap_{scene.index}.mp3")
        media.make_silence(silence, GAP_S)
        items.append(silence)
    full = os.path.join(workdir, "narration.wav")
    media.concat_audio(items, full)
    log(f"voiceover: {len(narrative.scenes)} scenes -> {full} ({start:.1f}s spoken)")
    return full