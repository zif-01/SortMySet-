import argparse
import json
import os
import secrets
import sys
from pathlib import Path

from .acquisition import download_track
from .features import analyze_local_audio, metadata_features
from .sequencing import build_sequence
from .xml_library import export_library, get_playlist_track_ids, load_library, location_to_path, select_playlist, track_metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sort an Apple Music XML playlist for DJ transitions")
    parser.add_argument("input", help="Apple Music exported XML/plist")
    parser.add_argument("-o", "--output", required=True, help="Output XML/plist")
    parser.add_argument("--playlist", help="Playlist name (defaults to first playlist)")
    parser.add_argument("--seed", type=int, default=None, help="Seed (default: cryptographically random)")
    parser.add_argument("--acquire-missing", action="store_true", help="Attempt opt-in yt-dlp download for unavailable tracks")
    parser.add_argument("--cache-dir", default="~/.cache/sortmyset", help="Directory for downloaded/cache audio")
    parser.add_argument(
        "--musicnn",
        metavar="MODEL",
        nargs="?",
        const="MTT_musicnn",
        choices=("MTT_musicnn", "MSD_musicnn"),
        help="Use musicnn tagging embeddings (MTT_musicnn or MSD_musicnn)",
    )
    parser.add_argument("--report", help="Optional JSON report path")
    return parser.parse_args(argv)


def resolve_seed(explicit_seed: int | None) -> int:
    return explicit_seed if explicit_seed is not None else secrets.randbelow(2**63)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        seed = resolve_seed(args.seed)
        library = load_library(args.input)
        playlist = select_playlist(library, args.playlist)
        track_ids = get_playlist_track_ids(playlist)
        if not track_ids:
            raise ValueError("Selected playlist contains no track IDs")

        features = []
        acquisition_report = []
        cache_dir = Path(args.cache_dir).expanduser()
        for track_id in track_ids:
            metadata = track_metadata(library, track_id)
            feature = metadata_features(track_id, metadata)
            location = metadata.get("Location")
            local_path = location_to_path(location) if isinstance(location, str) else None
            if local_path is not None and local_path.is_file():
                feature = analyze_local_audio(feature, local_path, args.musicnn)
            elif args.acquire_missing:
                result = download_track(track_id, feature.name, feature.artist, cache_dir)
                acquisition_report.append(result.__dict__)
                if result.path is not None:
                    feature = analyze_local_audio(feature, result.path, args.musicnn)
            features.append(feature)

        result, report = build_sequence(features, seed)
        export_library(library, playlist, list(report.sorted_order), args.output)

        report_payload = {
            "seed": report.seed,
            "original_order": list(report.original_order),
            "sorted_order": list(report.sorted_order),
            "average_bpm_change": report.average_bpm_change,
            "average_harmonic_cost": report.average_harmonic_cost,
            "average_energy_change": report.average_energy_change,
            "musicnn_model": args.musicnn,
            "musicnn_embedding_count": sum(
                feature.mood_embedding is not None for feature in features
            ),
            "acquisition": acquisition_report,
        }
        if args.report:
            Path(args.report).expanduser().write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
        print(json.dumps(report_payload, indent=2))
        return 0
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
