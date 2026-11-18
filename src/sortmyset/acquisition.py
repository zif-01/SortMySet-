from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AcquisitionResult:
    track_id: int
    status: str
    path: Path | None = None
    detail: str = ""


class AcquisitionDisabled(RuntimeError):
    pass


def download_track(track_id: int, title: str, artist: str, output_dir: str | Path) -> AcquisitionResult:
    if not shutil.which("yt-dlp"):
        return AcquisitionResult(track_id, "skipped", detail="yt-dlp is not installed")
    if not shutil.which("ffmpeg"):
        return AcquisitionResult(track_id, "skipped", detail="ffmpeg is not installed")

    destination = Path(output_dir).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    query = " ".join(part for part in (artist, title) if part)
    if not query:
        return AcquisitionResult(track_id, "skipped", detail="missing title and artist")

    command = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "wav",
        "--no-part",
        "--max-filesize", "100M",
        "--output", str(destination / f"{track_id}.%(ext)s"),
        f"ytsearch1:{query}",
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return AcquisitionResult(track_id, "failed", detail="download timed out")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        return AcquisitionResult(track_id, "failed", detail=detail[-500:])

    candidates = sorted(destination.glob(f"{track_id}.*"))
    for candidate in candidates:
        if candidate.suffix.lower() in {".wav", ".mp3", ".m4a", ".flac", ".ogg"}:
            return AcquisitionResult(track_id, "downloaded", candidate)
    return AcquisitionResult(track_id, "failed", detail="yt-dlp completed without a usable audio file")
