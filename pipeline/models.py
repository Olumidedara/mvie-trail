from dataclasses import dataclass, field


@dataclass
class SourceClip:
    url: str = ""
    provider: str = "pexels"
    width: int = 0
    height: int = 0
    duration: float = 0.0
    local_path: str = ""
    title: str = ""


@dataclass
class Scene:
    index: int = 0
    query: str = ""
    text: str = ""
    visual_hint: str = ""
    clip: SourceClip = field(default_factory=SourceClip)
    audio_path: str = ""
    duration: float = 0.0
    start: float = 0.0


@dataclass
class Narrative:
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    hook: str = ""
    scenes: list[Scene] = field(default_factory=list)

    @property
    def captions(self) -> str:
        return "\n\n".join(s.text for s in self.scenes if s.text)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "hook": self.hook,
            "scenes": [
                {
                    "index": s.index,
                    "query": s.query,
                    "text": s.text,
                    "visual_hint": s.visual_hint,
                    "duration": s.duration,
                    "start": s.start,
                }
                for s in self.scenes
            ],
        }