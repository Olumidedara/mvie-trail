import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..config import env


def find_binary(name: str) -> str:
    located = shutil.which(name)
    if located:
        return located
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
    configured = env("FFMPEG_PATH" if name == "ffmpeg" else "FFPROBE_PATH")
    if configured and Path(configured).exists():
        return configured
    return name


def ffmpeg() -> str:
    return find_binary("ffmpeg")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    default_io = {"capture_output": True, "text": True}
    default_io.update(kwargs)
    return subprocess.run(cmd, **default_io)


def probe(src: str) -> dict:
    res = run([ffmpeg(), "-hide_banner", "-i", src])
    info = {"duration": 0.0, "width": 0, "height": 0}
    for line in (res.stderr or "").splitlines():
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", line)
        if m:
            h, mi, s = m.groups()
            info["duration"] = int(h) * 3600 + int(mi) * 60 + float(s)
        m = re.search(r"(\d{3,4})x(\d{3,4})", line)
        if m and not info["width"]:
            info["width"] = int(m.group(1))
            info["height"] = int(m.group(2))
    return info


def download_http(url: str, dest: str, max_bytes: int = 200 * 1024 * 1024) -> str:
    import requests

    r = requests.get(url, stream=True, timeout=(15, 120))
    r.raise_for_status()
    length = int(r.headers.get("Content-Length") or 0)
    if length and length > max_bytes:
        r.close()
        raise RuntimeError(f"file too large ({length // 1024 // 1024}MB)")
    with open(dest, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            if chunk:
                f.write(chunk)
    r.close()
    return dest


def download_yt(url: str, dest_dir: str) -> str:
    import yt_dlp

    opts = {
        "outtmpl": os.path.join(dest_dir, "%(id)s.%(ext)s"),
        "format": "best[height<=1080]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def mute_and_cut(src: str, dest: str, start: float, duration: float) -> None:
    ss = max(0.0, start)
    cmd = [
        ffmpeg(),
        "-y",
        "-ss",
        f"{ss:.2f}",
        "-t",
        f"{max(0.2, duration):.2f}",
        "-i",
        src,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        dest,
    ]
    run(cmd).check_returncode()


def make_silence(dest: str, duration: float = 0.18) -> None:
    run(
        [
            ffmpeg(),
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=44100:cl=stereo",
            "-t",
            f"{duration:.2f}",
            dest,
        ]
    ).check_returncode()


def concat_files(files: list[str], dest: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{p}'\n")
        list_file = f.name
    try:
        cmd = [ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", dest]
        run(cmd).check_returncode()
    finally:
        try:
            os.unlink(list_file)
        except OSError:
            pass


def concat_audio(files: list[str], dest: str) -> None:
    wavs = []
    tmpdir = tempfile.gettempdir()
    try:
        for i, p in enumerate(files):
            w = os.path.join(tmpdir, f"ca_{os.getpid()}_{i}.wav")
            run([ffmpeg(), "-y", "-i", p, "-ar", "44100", "-ac", "2", w]).check_returncode()
            wavs.append(w)
        if len(wavs) == 1:
            with open(wavs[0], "rb") as fin, open(dest, "wb") as fout:
                fout.write(fin.read())
        else:
            inputs: list[str] = []
            for w in wavs:
                inputs += ["-i", w]
            fc = "".join(f"[{i}:a:0]" for i in range(len(wavs)))
            fc += f"concat=n={len(wavs)}:v=0:a=1[a]"
            run(
                [ffmpeg(), "-y", *inputs, "-filter_complex", fc, "-map", "[a]",
                 "-ar", "44100", "-ac", "2", dest]
            ).check_returncode()
    finally:
        for w in wavs:
            try:
                os.unlink(w)
            except OSError:
                pass