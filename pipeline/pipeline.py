import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import env, load_config
from pipeline.core import analyzer, assembler, discovery, media, scriptwriter, voiceover
from pipeline.publishers import manifest as manifest_mod
from pipeline.publishers import releases as releases_mod


def log(msg: str) -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def _download(candidate, workdir: str, prefix: str, deadline_s: float = 0) -> str:
    ext = ".mp4"
    if candidate.provider == "archive" and "/" in candidate.url:
        ext = os.path.splitext(candidate.url.split("/")[-1])[1] or ".mp4"
    if candidate.provider == "studio":
        return media.download_yt(candidate.url, workdir)
    dest = os.path.join(workdir, f"{prefix}_{candidate.provider}{ext}")
    media.download_http(candidate.url, dest, deadline_s=deadline_s)
    return dest


def build_entry(job_id: str, cfg: dict, genre: str, topic: str, narrative, workdir: str, pub: dict | None) -> dict:
    captions = "\n\n".join(f"{s.text}" for s in narrative.scenes)
    videos = {}
    for key in ("vertical", "landscape"):
        local = os.path.join(workdir, f"{job_id}_{key}.mp4")
        videos[key] = {"local": local}
        if pub and key in pub.get("assets", {}):
            videos[key]["browser_download_url"] = pub["assets"][key]["browser_download_url"]
    return {
        "id": job_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "genre": genre,
        "topic": topic,
        "title": narrative.title,
        "description": narrative.description,
        "tags": narrative.tags,
        "hook": narrative.hook,
        "captions": captions,
        "videos": videos,
        "styles": {"mood": "", "themes": ""},
        "release": {"html_url": pub["html_url"], "tag_name": pub["tag_name"]} if pub else None,
    }


def run_job(cfg: dict, genre: str, topic: str, job_id: str, skip_upload: bool) -> dict:
    base = Path(cfg["output"]["jobs_dir"])
    workdir = str(base / job_id)
    os.makedirs(workdir, exist_ok=True)

    disc = discovery.Discovery(cfg)

    candidate = disc.genre_candidate(genre)
    if candidate:
        log(f"analysis source: {candidate.provider} {candidate.url}")
        try:
            candidate.local_path = _download(candidate, workdir, "source", deadline_s=420)
        except Exception as exc:
            log(f"source download failed: {exc}")
            candidate.local_path = ""
    analysis = analyzer.analyze(cfg, candidate, log)
    log(f"analysis: mood={analysis.get('mood')} themes={analysis.get('themes')}")

    narrative = scriptwriter.build_narrative(cfg, analysis, genre, 1, log)
    log(f"narrative: '{narrative.title}' ({len(narrative.scenes)} scenes)")

    for scene in narrative.scenes:
        query = scene.query or scene.visual_hint or genre
        choices = disc.candidates(query, "landscape")
        chosen = None
        for candidate in choices[:3]:
            try:
                scene.clip.provider = candidate.provider
                scene.clip.url = candidate.url
                scene.clip.local_path = _download(candidate, workdir, f"clip_{scene.index}", deadline_s=180)
                chosen = candidate
                log(f"scene {scene.index}: {candidate.provider} {os.path.basename(scene.clip.local_path)}")
                break
            except Exception as exc:
                scene.clip.local_path = ""
                log(f"scene {scene.index}: candidate {candidate.provider} failed ({exc})")
        if not chosen:
            log(f"scene {scene.index}: no usable clip for '{query}'")

    voiceover.generate(cfg, narrative, workdir, log)

    out_vert = os.path.join(workdir, f"{job_id}_vertical.mp4")
    out_land = os.path.join(workdir, f"{job_id}_landscape.mp4")
    assembler.build(cfg, narrative, "vertical", workdir, out_vert, log)
    assembler.build(cfg, narrative, "landscape", workdir, out_land, log)
    log(f"rendered: {out_vert}")

    pub = None
    if env("GITHUB_ACTIONS") == "true" and not skip_upload:
        try:
            pub = releases_mod.upload(
                cfg,
                {"vertical": out_vert, "landscape": out_land},
                name=narrative.title,
                body=narrative.description + "\n\n" + narrative.captions,
            )
            log(f"published: {pub['html_url']}")
        except Exception as exc:
            log(f"release upload failed: {exc}")

    entry = build_entry(job_id, cfg, genre, topic, narrative, workdir, pub)
    manifest_path = os.path.join(cfg["output"]["dir"], "manifest.json")
    manifest_mod.append(manifest_path, entry)
    for p in Path(workdir).glob("*.raw.mp4"):
        p.unlink(missing_ok=True)
    log(f"job done: {job_id}")
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Trailer story automation pipeline")
    parser.add_argument("run", help="subcommand: run")
    parser.add_argument("--topic", default="")
    parser.add_argument("--genre", default="")
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--job-id", default="")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--config", default="")
    args = parser.parse_args()

    cfg = load_config(args.config or None)
    genres = cfg["source"]["genres"]
    genre = args.genre or env("PIPELINE_GENRE") or (genres[0] if genres else "vintage science fiction")
    topic = args.topic or env("PIPELINE_TOPIC") or genre
    count = max(1, args.count or int(env("PIPELINE_COUNT") or cfg["schedule"].get("max_videos_per_run", 3)))

    for i in range(count):
        job_id = args.job_id or f"{genre.replace(' ', '-')}-{time.strftime('%Y%m%d-%H%M%S')}-{i + 1}"
        try:
            run_job(cfg, genre, topic, job_id, args.no_upload)
        except Exception as exc:
            import traceback

            log(f"job {job_id} failed: {exc}")
            traceback.print_exc()


if __name__ == "__main__":
    main()