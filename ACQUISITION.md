# Acquisition policy

Missing or unavailable `Location` values trigger an optional acquisition mode. It
requires `--acquire-missing` and local `yt-dlp` plus `ffmpeg` executables.

SortMySet:

- Queries by artist and title only.
- Limits download size and duration through the caller process.
- Refuses to proceed with encrypted/DRM-protected extraction.
- Exits or skips cleanly when tools, network access, or a match are unavailable.
- Keeps downloaded files in a cache directory and does not alter the Apple library.
- Records acquisition status in the JSON report.

The repository does not verify rights. The operator remains responsible for terms,
licenses, copyrights, and local law.
