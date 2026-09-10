from urllib import parse

import requests

from ..config import env
from ..models import SourceClip

PEXELS_URL = "https://api.pexels.com/videos/search"
ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_META = "https://archive.org/metadata/{}"
ARCHIVE_VIDEO_FORMATS = {"h.264", "MPEG4", "512Kb MPEG4", "512kb MPEG4"}


class Discovery:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.pexels_key = env("PEXELS_API_KEY", "")
        self.max_candidates = int(cfg["source"].get("max_candidates_per_scene", 4))

    def pexels(self, query: str, orientation: str = "portrait") -> list[SourceClip]:
        if not self.pexels_key:
            return []
        params = {"query": query, "per_page": 12, "orientation": orientation}
        url = f"{PEXELS_URL}?{parse.urlencode(params)}"
        try:
            r = requests.get(url, headers={"Authorization": self.pexels_key}, timeout=30)
            r.raise_for_status()
            payload = r.json()
        except requests.RequestException:
            return []
        clips = []
        for v in payload.get("videos", []):
            files = [f for f in v.get("video_files", []) if f.get("link")]
            files.sort(key=lambda f: (-(f.get("height") or 0), -(f.get("width") or 0), f.get("quality", "")))
            pick = None
            for f in files:
                w, h = (f.get("width") or 0), (f.get("height") or 0)
                if orientation == "portrait" and h >= w and h >= 720:
                    pick = f
                    break
                if orientation == "landscape" and w >= h and w >= 720:
                    pick = f
                    break
            if not pick:
                continue
            clips.append(
                SourceClip(
                    url=pick["link"],
                    provider="pexels",
                    width=v.get("width") or 0,
                    height=v.get("height") or 0,
                    duration=v.get("duration") or 0.0,
                    title=f"pexels-{v.get('id')}",
                )
            )
        min_dur = float(self.cfg["source"].get("pexels_min_duration", 5))
        return [c for c in clips if c.duration >= min_dur][: self.max_candidates]

    def archive(self, query: str) -> list[SourceClip]:
        collections = self.cfg["source"].get("archive_collections", ["prelinger"])
        q = f'({query}) AND collection:({" OR ".join(collections)})'
        params = {"q": q, "fl[]": "identifier", "rows": 8, "output": "json"}
        url = f"{ARCHIVE_SEARCH}?{parse.urlencode({'q': q})}"
        try:
            r = requests.get(
                url,
                params={"fl[]": "identifier", "rows": 8, "output": "json"},
                timeout=30,
            )
            r.raise_for_status()
            docs = r.json().get("response", {}).get("docs", [])
        except requests.RequestException:
            return []
        clips = []
        for d in docs:
            ident = d.get("identifier")
            if not ident:
                continue
            try:
                meta = requests.get(ARCHIVE_META.format(ident), timeout=30).json()
            except requests.RequestException:
                continue
            for f in meta.get("files", []):
                fmt = f.get("format", "")
                if fmt not in ARCHIVE_VIDEO_FORMATS:
                    continue
                name = f.get("name", "")
                if not name.lower().endswith((".mp4", ".ogv")):
                    continue
                dur = (f.get("length") or "0").split(":")[-1]
                try:
                    duration = float(dur)
                except ValueError:
                    duration = 0.0
                size = int(f.get("size") or 0)
                if size and size > 60 * 1024 * 1024:
                    continue
                clips.append(
                    SourceClip(
                        url=f"https://archive.org/download/{ident}/{name}",
                        provider="archive",
                        width=int(f.get("width") or 0),
                        height=int(f.get("height") or 0),
                        duration=duration,
                        title=ident,
                    )
                )
                break
        return clips[: self.max_candidates]

    def studio(self, query: str) -> list[SourceClip]:
        import yt_dlp

        if not self.cfg["source"].get("use_studio_trailers"):
            return []
        opts = {"quiet": True, "no_warnings": True, "format": "best"}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch{self.max_candidates}:{query} official trailer", download=False)
        except Exception:
            return []
        clips = []
        for e in info.get("entries", []):
            if not e or e.get("duration") is None:
                continue
            if e["duration"] < 20 or e["duration"] > 420:
                continue
            clips.append(
                SourceClip(
                    url=e.get("webpage_url", ""),
                    provider="studio",
                    duration=float(e["duration"]),
                    title=e.get("title", ""),
                )
            )
        return clips[: self.max_candidates]

    def candidates(self, query: str, orientation: str = "portrait") -> list[SourceClip]:
        return self.pexels(query, orientation) + self.archive(query) + self.studio(query)

    def genre_candidate(self, genre: str) -> SourceClip | None:
        if self.cfg["source"].get("use_studio_trailers"):
            found = self.studio(genre)
            if found:
                return found[0]
        found = self.archive(genre)
        if found:
            return found[0]
        pex = self.pexels(f"{genre} cinematic", "landscape")
        if pex:
            return pex[0]
        return None