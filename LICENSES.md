# Third-party considerations

SortMySet's initial implementation uses Python standard-library `plistlib` and
optional `librosa`. Those dependencies and downloadable audio may have separate
license or terms requirements.

- `librosa` is BSD-licensed, but model and data dependencies may impose their own
  terms.
- `musicnn` is ISC-licensed. Its legacy 0.1.0 package metadata declares TensorFlow
  1.x and NumPy 1.x constraints that are superseded in this project by the
  compatibility install file and TensorFlow 2 compat mode. Model weights and
  training datasets remain subject to upstream terms.
- Essentia is AGPLv3 and is not enabled in the initial implementation.
- `yt-dlp` and `ffmpeg` are external tools. SortMySet does not grant rights to
  media downloaded with them.
- Apple Music and YouTube service terms must be reviewed before acquisition.
