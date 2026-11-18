import os
import plistlib
from pathlib import Path
from urllib.parse import unquote, urlparse


def location_to_path(location: str) -> Path | None:
    if not location:
        return None
    parsed = urlparse(location)
    if parsed.scheme == "file":
        path = unquote(parsed.path)
        if parsed.netloc and parsed.netloc != "localhost":
            path = f"//{parsed.netloc}{path}"
        return Path(path)
    if parsed.scheme:
        return None
    return Path(location).expanduser()


def load_library(path: str | os.PathLike[str]) -> dict:
    with open(path, "rb") as handle:
        library = plistlib.load(handle)
    if not isinstance(library, dict):
        raise ValueError("The Apple Music export is not a property-list dictionary")
    if "Tracks" not in library:
        raise ValueError("The Apple Music export has no Tracks dictionary")
    return library


def select_playlist(library: dict, name: str | None = None) -> dict:
    playlists = library.get("Playlists", [])
    if not playlists:
        raise ValueError("The Apple Music export has no playlists")
    if name:
        matches = [item for item in playlists if item.get("Name") == name]
        if not matches:
            raise ValueError(f"Playlist not found: {name}")
        return matches[0]
    return playlists[0]


def get_playlist_track_ids(playlist: dict) -> list[int]:
    track_ids: list[int] = []
    for item in playlist.get("Playlist Items", []):
        track_id = item.get("Track ID")
        if isinstance(track_id, int):
            track_ids.append(track_id)
    return track_ids


def track_metadata(library: dict, track_id: int) -> dict:
    tracks = library["Tracks"]
    value = tracks.get(str(track_id)) or tracks.get(track_id)
    if not isinstance(value, dict):
        raise KeyError(track_id)
    return value


def export_library(library: dict, playlist: dict, track_ids: list[int], output: str | os.PathLike[str]) -> None:
    existing_items = playlist.get("Playlist Items", [])
    available_items = {}
    for item in existing_items:
        if isinstance(item, dict) and isinstance(item.get("Track ID"), int):
            available_items.setdefault(item["Track ID"], []).append(item)
    items = []
    used_counts = {}
    for track_id in track_ids:
        count = used_counts.get(track_id, 0)
        candidates = available_items.get(track_id, [])
        if count < len(candidates):
            item = dict(candidates[count])
            item["Track ID"] = track_id
        else:
            item = {"Track ID": track_id}
        items.append(item)
        used_counts[track_id] = count + 1
    playlist["Playlist Items"] = items
    with open(output, "wb") as handle:
        plistlib.dump(library, handle, fmt=plistlib.FMT_XML, sort_keys=False)
