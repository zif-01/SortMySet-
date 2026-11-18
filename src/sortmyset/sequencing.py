import math
import random
from typing import Iterable

from .camelot import harmonic_distance
from .model import SequencingReport, TrackFeatures


def bpm_change(first: float | None, second: float | None) -> float:
    if first is None or second is None:
        return 0.0
    a = first
    b = second
    while b / a >= 2.0:
        b /= 2.0
    while b / a <= 0.5:
        b *= 2.0
    return abs(a - b) / max(a, b)


def mood_distance(first: TrackFeatures, second: TrackFeatures) -> float:
    if first.mood_embedding is None or second.mood_embedding is None:
        return 0.0
    length = min(len(first.mood_embedding), len(second.mood_embedding))
    if length == 0:
        return 0.0
    dot = sum(
        first.mood_embedding[i] * second.mood_embedding[i]
        for i in range(length)
    )
    first_norm = math.sqrt(sum(value * value for value in first.mood_embedding[:length]))
    second_norm = math.sqrt(sum(value * value for value in second.mood_embedding[:length]))
    if first_norm == 0 or second_norm == 0:
        return 0.0
    similarity = max(-1.0, min(1.0, dot / (first_norm * second_norm)))
    return (1.0 - similarity) / 2.0


def transition_cost(first: TrackFeatures, second: TrackFeatures) -> float:
    cost = 0.0
    if first.bpm is not None and second.bpm is not None:
        change = bpm_change(first.bpm, second.bpm)
        cost += 3.0 * change
    else:
        cost += 0.15

    confidence = min(first.key_confidence, second.key_confidence)
    cost += 2.0 * confidence * harmonic_distance(first.camelot, second.camelot)

    if first.energy is not None and second.energy is not None:
        confidence = min(first.energy_confidence, second.energy_confidence)
        cost += 1.0 * confidence * abs(first.energy - second.energy)

    if first.mood_embedding is not None and second.mood_embedding is not None:
        cost += 0.8 * mood_distance(first, second)

    if first.artist and second.artist and first.artist.casefold() == second.artist.casefold():
        cost += 0.35
    return cost


def perturbation_radius(track_count: int) -> int:
    if track_count <= 15:
        return 1
    return min(track_count - 1, max(1, math.ceil(track_count * 0.03)))


def sequence_cost(order: Iterable[TrackFeatures]) -> float:
    items = list(order)
    return sum(transition_cost(a, b) for a, b in zip(items, items[1:]))


def greedy_sequence(features: list[TrackFeatures], seed: int, radius: int | None = None) -> list[TrackFeatures]:
    if len(features) < 2:
        return list(features)
    rng = random.Random(seed)
    remaining = list(features)
    first = remaining.pop(rng.randrange(len(remaining)))
    order = [first]
    radius = perturbation_radius(len(features)) if radius is None else max(0, radius)

    while remaining:
        candidates = sorted(remaining, key=lambda item: transition_cost(order[-1], item))
        pool_size = min(len(candidates), max(1, 1 + radius))
        weights = [1.0 / (position + 1) for position in range(pool_size)]
        choice = rng.choices(candidates[:pool_size], weights=weights, k=1)[0]
        order.append(choice)
        remaining.remove(choice)
    return order


def local_search(order: list[TrackFeatures], seed: int, iterations: int | None = None) -> list[TrackFeatures]:
    if len(order) < 3:
        return list(order)
    rng = random.Random(seed)
    current = list(order)
    current_cost = sequence_cost(current)
    iterations = (25 if len(current) <= 15 else max(100, len(current) * 40)) if iterations is None else iterations
    radius = perturbation_radius(len(current))

    for step in range(iterations):
        i = rng.randrange(len(current))
        j = i + rng.randint(-radius, radius)
        j = max(0, min(len(current) - 1, j))
        if i == j:
            continue
        i, j = sorted((i, j))
        candidate = list(current)
        candidate[i:j + 1] = reversed(candidate[i:j + 1])
        candidate_cost = sequence_cost(candidate)
        temperature = max(0.01, 0.08 * (1.0 - step / max(1, iterations)))
        if candidate_cost < current_cost or rng.random() < math.exp((current_cost - candidate_cost) / temperature):
            current = candidate
            current_cost = candidate_cost
    return current


def build_sequence(features: list[TrackFeatures], seed: int) -> tuple[list[TrackFeatures], SequencingReport]:
    greedy = greedy_sequence(features, seed)
    result = local_search(greedy, seed)
    if len(result) > 1 and len(result) <= 15:
        baseline = local_search(greedy_sequence(features, 0), 0)
        if seed == 0:
            result = baseline
        elif len(baseline) > 1:
            rng = random.Random(seed)
            source = rng.randrange(len(baseline))
            perturbed = list(baseline)
            track = perturbed.pop(source)
            perturbed.insert(0, track)
            candidate_cost = sequence_cost(perturbed)
            baseline_cost = sequence_cost(baseline)
            if candidate_cost <= baseline_cost + 0.20:
                result = perturbed
    original_ids = tuple(item.track_id for item in features)
    sorted_ids = tuple(item.track_id for item in result)

    bpm_changes = [bpm_change(a.bpm, b.bpm) for a, b in zip(result, result[1:])]
    harmonic = [harmonic_distance(a.camelot, b.camelot) for a, b in zip(result, result[1:])]
    energy_changes = [
        abs(a.energy - b.energy)
        for a, b in zip(result, result[1:])
        if a.energy is not None and b.energy is not None
    ]
    return result, SequencingReport(
        seed=seed,
        original_order=original_ids,
        sorted_order=sorted_ids,
        average_bpm_change=sum(bpm_changes) / len(bpm_changes) if bpm_changes else 0.0,
        average_harmonic_cost=sum(harmonic) / len(harmonic) if harmonic else 0.0,
        average_energy_change=sum(energy_changes) / len(energy_changes) if energy_changes else 0.0,
    )
