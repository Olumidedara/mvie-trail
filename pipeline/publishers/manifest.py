import json
import os
from pathlib import Path

MAX_ENTRIES = 200


def read(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    return data if isinstance(data, list) else []


def append(path: str, entry: dict) -> None:
    entries = read(path)
    entries.insert(0, entry)
    entries = entries[:MAX_ENTRIES]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def find(path: str, job_id: str) -> dict | None:
    for e in read(path):
        if e.get("id") == job_id:
            return e
    return None