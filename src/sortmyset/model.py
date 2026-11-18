from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TrackFeatures:
    track_id: int
    name: str = ""
    artist: str = ""
    album: str = ""
    bpm: Optional[float] = None
    camelot: Optional[str] = None
    energy: Optional[float] = None
    bpm_confidence: float = 0.0
    key_confidence: float = 0.0
    energy_confidence: float = 0.0
    mood_embedding: Optional[tuple[float, ...]] = None


@dataclass(frozen=True)
class SequencingReport:
    seed: int
    original_order: tuple[int, ...]
    sorted_order: tuple[int, ...]
    average_bpm_change: float
    average_harmonic_cost: float
    average_energy_change: float
