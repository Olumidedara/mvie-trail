import os
import time

import requests

from ..config import env


def _token() -> str:
    return env("GITHUB_TOKEN", "") or env("GH_PAT", "")


def _repo(cfg: dict) -> str:
    return cfg["publisher"].get("github_repo", "") or env("GITHUB_REPOSITORY", "")


def upload(
    cfg: dict,
    files: dict[str, str],
    name: str,
    body: str,
):
    repo = _repo(cfg)
    token = _token()
    if not repo or not token:
        raise RuntimeError("publishing requires GITHUB_REPOSITORY and GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    tag = f"v{int(time.time() * 1000)}"
    r = requests.post(
        f"https://api.github.com/repos/{repo}/releases",
        headers=headers,
        json={"tag_name": tag, "name": name, "body": body, "draft": False, "prerelease": False},
        timeout=60,
    )
    r.raise_for_status()
    release = r.json()
    upload_base = release["upload_url"].replace("{?name,label}", "")
    assets = {}
    for key, path in files.items():
        with open(path, "rb") as f:
            data = f.read()
        r2 = requests.post(
            upload_base,
            params={"name": os.path.basename(path)},
            headers={**headers, "Content-Type": "video/mp4"},
            data=data,
            timeout=600,
        )
        r2.raise_for_status()
        asset = r2.json()
        assets[key] = {
            "browser_download_url": asset.get("browser_download_url", ""),
            "url": asset.get("url", ""),
        }
    return {"html_url": release.get("html_url", ""), "tag_name": tag, "assets": assets}