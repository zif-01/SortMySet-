from __future__ import annotations

from pathlib import Path

from .camelot import camelot_key
from .model import TrackFeatures


def metadata_features(track_id: int, metadata: dict) -> TrackFeatures:
    bpm = metadata.get("BPM")
    try:
        bpm_value = float(bpm) if bpm is not None else None
    except (TypeError, ValueError):
        bpm_value = None

    return TrackFeatures(
        track_id=track_id,
        name=str(metadata.get("Name", "")),
        artist=str(metadata.get("Artist", "")),
        album=str(metadata.get("Album", "")),
        bpm=bpm_value,
        camelot=_metadata_camelot(metadata),
        energy=_metadata_energy(metadata),
        bpm_confidence=0.7 if bpm_value is not None else 0.0,
        key_confidence=0.5 if _metadata_camelot(metadata) else 0.0,
        energy_confidence=0.3 if _metadata_energy(metadata) is not None else 0.0,
    )


def musicnn_embedding(path: Path, model: str = "MTT_musicnn") -> tuple[float, ...] | None:
    try:
        from musicnn.extractor import extractor
    except ImportError:
        return None

    try:
        taggram, tags = extractor(
            str(path),
            model=model,
            input_length=3,
            extract_features=False,
        )
    except (ValueError, RuntimeError, OSError):
        return None

    if len(tags) == 0:
        return None
    rows = [list(row) for row in taggram]
    if not rows or not rows[0]:
        return None
    dimensions = len(rows[0])
    mean_tag_scores = [
        sum(float(row[index]) for row in rows) / len(rows)
        for index in range(dimensions)
    ]
    norm = sum(value * value for value in mean_tag_scores) ** 0.5
    if norm == 0:
        return None
    return tuple(float(value / norm) for value in mean_tag_scores)


def _metadata_camelot(metadata: dict) -> str | None:
    for field in ("Key", "Camelot", "Camelot Key", "Initial Key"):
        value = metadata.get(field)
        if isinstance(value, str) and value:
            stripped = value.strip().upper()
            if len(stripped) <= 3 and stripped[-1:] in {"A", "B"}:
                return stripped
            return camelot_key(stripped)
    return None


def _metadata_energy(metadata: dict) -> float | None:
    for field in ("Energy", "Energy Level", "Intensity"):
        value = metadata.get(field)
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if 1.0 <= number <= 10.0:
            return (number - 1.0) / 9.0
        if 0.0 <= number <= 1.0:
            return number
    return None


def analyze_local_audio(
    track: TrackFeatures,
    path: Path,
    musicnn_model: str | None = None,
) -> TrackFeatures:
    try:
        import librosa
        import numpy as np
    except ImportError:
        return track

    y, sr = librosa.load(str(path), sr=22050, mono=True)
    if y.size < sr:
        return track

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(np.asarray(tempo).reshape(-1)[0])
    onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.clip((np.mean(rms) + 0.5 * np.mean(onset_strength)) / 1.5, 0.0, 1.0))

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    profile = np.asarray([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    chroma_mean = np.mean(chroma, axis=1)
    correlations = []
    for tonic in range(12):
        major_profile = np.roll(profile, tonic)
        minor_profile = np.roll(np.asarray([2.91, 4.68, 2.88, 5.38, 2.60, 4.35, 3.32, 2.94, 3.97, 4.11, 3.00, 3.71]), tonic)
        correlations.append((float(np.corrcoef(chroma_mean, major_profile)[0, 1]), tonic, "major"))
        correlations.append((float(np.corrcoef(chroma_mean, minor_profile)[0, 1]), tonic, "minor"))
    score, tonic, scale = max(correlations)
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    key = camelot_key(names[tonic], scale)

    beat_confidence = float(np.clip(np.mean(librosa.util.peak_pick(onset_strength, 3, 3, 3, 5, 0.5, 10)) if onset_strength.size else 0.5, 0.0, 1.0))
    bpm_confidence = 0.8 if bpm > 0 else 0.0
    embedding = musicnn_embedding(path, musicnn_model) if musicnn_model else None
    return TrackFeatures(
        track_id=track.track_id,
        name=track.name,
        artist=track.artist,
        album=track.album,
        bpm=bpm,
        camelot=key,
        energy=energy,
        bpm_confidence=bpm_confidence,
        key_confidence=float(np.clip((score + 1.0) / 2.0, 0.0, 1.0)),
        energy_confidence=0.8,
        mood_embedding=embedding,
    )
