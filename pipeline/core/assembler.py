import os

from ..models import Narrative
from . import media
from .voiceover import GAP_S


def _ts(seconds: float) -> str:
    cs = int(round(seconds * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _escape_filter_path(path: str) -> str:
    p = path.replace("\\", "/")
    p = p.replace("'", "\\'")
    p = p.replace(":", "\\:")
    return p


def _build_ass(cfg: dict, narrative: Narrative, w: int, h: int, cap_size: int, path: str) -> None:
    cap = cfg["video"]
    outline = max(2, cap_size // 12)
    margin_v = int(h * 0.12)
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "Collisions: Normal",
        f"PlayResX: {w}",
        f"PlayResY: {h}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,Arial,{cap_size},&H00FFFFFF,&H000000FF,&H00111111,&H96000000,0,0,0,0,100,100,0,0,1,{outline},0,2,80,80,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for scene in narrative.scenes:
        if not scene.text:
            continue
        if scene.start <= 0:
            start = 0.4
        else:
            start = max(0.2, scene.start + 0.15)
        end = scene.start + scene.duration - 0.15
        if end <= start:
            end = start + 1.0
        text = scene.text.replace("{", "(").replace("}", ")").replace("\n", " ")
        lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Default,,0,0,0,,{text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _render_scene(src: str | None, dest: str, dur: float, w: int, h: int, fps: int, ken: bool, log) -> None:
    tmp = dest + ".raw.mp4"
    if src and os.path.exists(src):
        from_begin = ""
        duration = media.probe(src).get("duration", dur) or dur
        if duration > 2.0:
            from_begin = ["-ss", "0.75"]
        clip_dur = min(duration, dur)
        factor = dur / clip_dur if clip_dur > 0 else 1.0
        vf = (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h}:(iw-ow)/2:(ih-oh)/2,"
            f"fps={fps},format=yuv420p"
        )
        if factor < 0.9 or factor > 1.05:
            vf += f",setpts={factor:.4f}*PTS"
        cmd = [media.ffmpeg(), "-y", "-t", f"{dur:.2f}", *from_begin, "-i", src, "-vf", vf,
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", tmp]
        res = media.run(cmd)
        if res.returncode != 0:
            log(f"clip render warning: {res.stderr[-400:]}")
            src = None
    if not src or not os.path.exists(src):
        cmd = [media.ffmpeg(), "-y", "-f", "lavfi", "-i", f"color=c=0x141a26:s={w}x{h}:d={dur:.2f}:r={fps}",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp]
        media.run(cmd).check_returncode()
    if ken:
        frames = max(1, int(round(dur * fps)))
        step = 0.12 / frames
        zf = (
            f"zoompan=z='min(zoom+{step:.6f},1.12)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d=1:s={w}x{h}:fps={fps},format=yuv420p"
        )
        media.run([media.ffmpeg(), "-y", "-i", tmp, "-vf", zf,
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", dest]).check_returncode()
    else:
        media.run([media.ffmpeg(), "-y", "-i", tmp, "-c", "copy", dest]).check_returncode()
    for p in (tmp,):
        if os.path.exists(p):
            os.unlink(p)


def build(cfg: dict, narrative: Narrative, orientation: str, workdir: str, out_path: str, log) -> str:
    vcfg = cfg["video"][orientation]
    w, h, fps = vcfg["width"], vcfg["height"], vcfg["fps"]
    ken = bool(cfg["video"].get("ken_burns", True))
    cap_enabled = bool(cfg["video"].get("captions_enabled", True))
    log(f"assembling {orientation} {w}x{h} @ {fps}fps (kenburns={ken}, captions={cap_enabled})")

    intermediates = []
    lasts = len(narrative.scenes) - 1
    for scene in narrative.scenes:
        dur = scene.duration if scene.index >= lasts else scene.duration + GAP_S
        dest = os.path.join(workdir, f"{orientation}_s{scene.index}.mp4")
        _render_scene(scene.clip.local_path, dest, max(1.2, dur), w, h, fps, ken, log)
        intermediates.append(dest)

    concat_path = os.path.join(workdir, f"{orientation}_concat.mp4")
    media.concat_files(intermediates, concat_path)

    ass_path = None
    if cap_enabled:
        cap_size = int(vcfg.get("caption_font_size", cfg["video"].get("caption_font_size", 58)))
        if orientation == "landscape":
            cap_size = int(cap_size * 0.8)
        ass_path = os.path.join(workdir, f"{orientation}_captions.ass")
        _build_ass(cfg, narrative, w, h, cap_size, ass_path)

    narration = os.path.join(workdir, "narration.wav")
    args = [media.ffmpeg(), "-y", "-i", concat_path, "-i", narration]
    if ass_path:
        escaped = _escape_filter_path(ass_path)
        fstyle = f"Fontname=Arial,Fontsize=0"
        vf = f"[0:v]subtitles=filename='{escaped}'[v]"
        args += ["-filter_complex", vf, "-map", "[v]"]
    else:
        args += ["-map", "0:v"]
    args += ["-map", "1:a", "-shortest",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_path]
    media.run(args).check_returncode()
    log(f"{orientation} written: {out_path}")
    return out_path