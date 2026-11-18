import plistlib
import tempfile
import unittest
from pathlib import Path

from sortmyset.camelot import camelot_key, harmonic_distance
from sortmyset.model import TrackFeatures
from sortmyset.sequencing import (
    bpm_change,
    build_sequence,
    perturbation_radius,
)
from sortmyset.xml_library import (
    export_library,
    get_playlist_track_ids,
    load_library,
    location_to_path,
    select_playlist,
)


def library_data():
    return {
        "Library Persistent ID": "TEST",
        "Tracks": {
            "101": {"Name": "One", "Artist": "A", "BPM": 128, "Location": "file:///music/1.mp3", "Camelot": "8A"},
            "102": {"Name": "Two", "Artist": "B", "BPM": 130, "Location": "file:///music/2.mp3", "Camelot": "9A"},
        },
        "Playlists": [{"Name": "Test", "Playlist Items": [{"Track ID": 101}, {"Track ID": 102}]}],
    }


class SortMySetTests(unittest.TestCase):
    def test_location_conversion(self):
        self.assertEqual(location_to_path("file:///tmp/a%20b.mp3"), Path("/tmp/a b.mp3"))
        self.assertIsNone(location_to_path("https://example.com/a"))
        self.assertEqual(location_to_path("/tmp/a.mp3"), Path("/tmp/a.mp3"))

    def test_playlist_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.xml"
            output = Path(directory) / "output.xml"
            with source.open("wb") as handle:
                plistlib.dump(library_data(), handle, fmt=plistlib.FMT_XML)
            library = load_library(source)
            playlist = select_playlist(library, "Test")
            self.assertEqual(get_playlist_track_ids(playlist), [101, 102])
            export_library(library, playlist, [102, 101], output)
            reloaded = load_library(output)
            self.assertEqual(get_playlist_track_ids(select_playlist(reloaded, "Test")), [102, 101])
            self.assertEqual(reloaded["Tracks"]["101"]["Name"], "One")

    def test_missing_playlist(self):
        with self.assertRaisesRegex(ValueError, "Playlist not found"):
            select_playlist(library_data(), "Missing")

    def test_camelot_and_bpm(self):
        self.assertEqual(camelot_key("A", "minor"), "8A")
        self.assertEqual(camelot_key("C", "major"), "8B")
        self.assertEqual(harmonic_distance("8A", "8A"), 0.0)
        self.assertEqual(harmonic_distance("8A", "8B"), 0.15)
        self.assertEqual(harmonic_distance("8A", "9A"), 0.25)
        self.assertEqual(bpm_change(128.0, 64.0), 0.0)
        self.assertGreater(bpm_change(128.0, 140.0), 0.08)

    def test_reproducible_sequence_and_size_scaling(self):
        features = [
            TrackFeatures(
                track_id=i,
                bpm=120.0 + i % 8,
                camelot=f"{(i % 12) + 1}A",
                energy=(i % 10) / 10,
            )
            for i in range(15)
        ]
        first, report = build_sequence(features, 42)
        second, _ = build_sequence(features, 42)
        self.assertEqual(
            [item.track_id for item in first],
            [item.track_id for item in second],
        )
        self.assertEqual(report.sorted_order, tuple(item.track_id for item in first))
        self.assertEqual(perturbation_radius(15), 1)
        self.assertGreaterEqual(perturbation_radius(100), perturbation_radius(15))


if __name__ == "__main__":
    unittest.main()
