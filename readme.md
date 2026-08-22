[![Tests](https://github.com/Mrchazaaa/track-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/Mrchazaaa/track-automation/actions/workflows/tests.yml)

## Setup

1. Install [Poetry](https://python-poetry.org/docs/#installation).
2. Install the Python dependencies: `poetry install`.
3. Copy `config.env.example` to `config.env` and set your LALAL.AI API key.
4. Run, for example: `poetry run ./get_track.sh "https://www.youtube.com/watch?v=5JUjFN9AuFU" "GodGaveMeFeetForDancing"`. This wrapper creates a vocals-and-drums track.

## Selecting instruments

`--include` is required and makes an output track containing only the requested stems. The
stems are extracted with LALAL.AI and mixed into one track with ffmpeg:

```bash
poetry run python -m track_automation.cli --input-file song.mp3 --include drums voice guitar
```

For a video URL, place the URL and output name before `--include`:

```bash
poetry run python -m track_automation.cli "https://example.com/video" "song" --include drums voice
```

`drums`/`drum`, `voice`/`vocals`, `guitar`, `bass`, and `piano` are supported.

## Testing

Run the automated tests with:

```bash
poetry run python -m unittest discover -s tests -v
```

`config.env` is intentionally ignored and must not be committed.

## Usage rights

You are responsible for ensuring that downloading, processing, and using audio complies with the relevant platform terms and with applicable copyright and other rights.
