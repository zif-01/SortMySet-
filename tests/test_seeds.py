import unittest
import sys
import types
from pathlib import Path
from unittest.mock import patch

from sortmyset.model import TrackFeatures
from sortmyset.features import musicnn_embedding
from sortmyset.sequencing import build_sequence, mood_distance
from sortmyset.cli import parse_args, resolve_seed


class SeedTests(unittest.TestCase):
    def make_features(self, count):
        return [
            TrackFeatures(
                track_id=i,
                bpm=120 + i % 8,
                camelot=f"{i % 12 + 1}A",
                energy=i / max(count - 1, 1),
                key_confidence=0.5,
                energy_confidence=0.5,
            )
            for i in range(count)
        ]

    def test_small_seed_variation_is_one_move(self):
        features = self.make_features(15)
        base, _ = build_sequence(features, 0)
        varied, _ = build_sequence(features, 42)

        baseline_ids = [item.track_id for item in base]
        varied_ids = [item.track_id for item in varied]
        displaced = [item for item in baseline_ids if item not in set(varied_ids)]
        self.assertEqual(displaced, [])
        distance = sum(a != b for a, b in zip(baseline_ids, varied_ids))
        self.assertLessEqual(distance, 15)

    def test_seed_reproducibility(self):
        features = self.make_features(40)
        first, _ = build_sequence(features, 123)
        second, _ = build_sequence(features, 123)
        self.assertEqual(
            [item.track_id for item in first],
            [item.track_id for item in second],
        )

    def test_first_track_depends_on_seed(self):
        features = self.make_features(20)
        first_a, _ = build_sequence(features, 100)
        first_b, _ = build_sequence(features, 101)
        self.assertNotEqual(first_a[0].track_id, first_b[0].track_id)

    def test_unspecified_seed_is_random(self):
        args = parse_args(["Library.xml", "--output", "Sorted.xml"])
        self.assertIsNone(args.seed)

    def test_random_seed_is_generated_when_missing(self):
        seeds = {resolve_seed(None) for _ in range(8)}
        self.assertGreater(len(seeds), 1)
        self.assertEqual(resolve_seed(123), 123)

    def test_musicnn_embedding_uses_mean_normalized_taggram(self):
        musicnn_module = types.ModuleType("musicnn")
        extractor_module = types.ModuleType("musicnn.extractor")
        extractor_module.extractor = lambda *args, **kwargs: (
            [[0.5, 0.0], [1.0, 0.5]],
            ["dance", "electronic"],
        )

        with patch.dict(
            sys.modules,
            {
                "musicnn": musicnn_module,
                "musicnn.extractor": extractor_module,
            },
        ):
            embedding = musicnn_embedding(Path("/tmp/mock.wav"))

        self.assertIsNotNone(embedding)
        self.assertEqual(len(embedding), 2)
        self.assertAlmostEqual(sum(value * value for value in embedding), 1.0)

    def test_mood_distance_prefers_similar_embeddings(self):
        similar_first = TrackFeatures(track_id=1, mood_embedding=(1.0, 0.0))
        similar_second = TrackFeatures(track_id=2, mood_embedding=(0.9, 0.1))
        opposite = TrackFeatures(track_id=3, mood_embedding=(0.0, 1.0))
        self.assertLess(
            mood_distance(similar_first, similar_second),
            mood_distance(similar_first, opposite),
        )


if __name__ == "__main__":
    unittest.main()
