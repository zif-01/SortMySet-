KEY_TO_CAMELOT = {
    "C": "8B", "A": "8A",
    "G": "9B", "E": "9A",
    "D": "10B", "B": "10A",
    "A#": "11B", "F#": "11A",
    "BB": "3B", "GB": "6A",
    "F": "12B", "D": "12A",
    "C#": "4A", "A#": "11B",
}


def camelot_key(key: str, scale: str = "") -> str | None:
    if not key:
        return None
    normalized = key.strip().replace("♯", "#").replace("♭", "b").upper()
    if normalized in {"C#", "DB"}:
        normalized = "C#"
    if normalized in {"D#", "EB"}:
        normalized = "EB"
    if normalized in {"F#", "GB"}:
        normalized = "F#"
    if normalized in {"G#", "AB"}:
        normalized = "G#"
    if normalized in {"A#", "BB"}:
        normalized = "A#"
    scale = scale.strip().lower()
    if scale == "minor":
        # Minor-key Camelot mapping.
        minor = {"C": "5A", "C#": "12A", "D": "7A", "D#": "3A",
                 "E": "9A", "F": "11A", "F#": "2A", "G": "10A",
                 "G#": "1A", "A": "8A", "A#": "3A", "B": "10A"}
        return minor.get(normalized)
    if scale == "major":
        major = {"C": "8B", "C#": "3B", "D": "10B", "D#": "5B",
                 "E": "12B", "F": "7B", "F#": "2B", "G": "9B",
                 "G#": "4B", "A": "11B", "A#": "6B", "B": "1B"}
        return major.get(normalized)
    return KEY_TO_CAMELOT.get(normalized)


def harmonic_distance(first: str | None, second: str | None) -> float:
    if not first or not second:
        return 0.45
    if first == second:
        return 0.0
    if first[-1] != second[-1] and first[:-1] == second[:-1]:
        return 0.15
    try:
        a = int(first[:-1])
        b = int(second[:-1])
    except (TypeError, ValueError):
        return 1.0
    distance = min((a - b) % 12, (b - a) % 12)
    if distance == 1:
        return 0.25
    if distance == 2:
        return 0.55
    return 0.9
