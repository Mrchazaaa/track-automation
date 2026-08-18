[![Tests](https://github.com/Mrchazaaa/track-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/Mrchazaaa/track-automation/actions/workflows/tests.yml)

## Setup

1. Install [Poetry](https://python-poetry.org/docs/#installation).
2. Install the Python dependencies: `poetry install`.
3. Copy `config.env.example` to `config.env` and set your LALAL.AI API key.
4. Run, for example: `poetry run ./get_track.sh "https://www.youtube.com/watch?v=5JUjFN9AuFU" "GodGaveMeFeetForDancing"`.

## Testing

Run the automated tests with:

```bash
poetry run python -m unittest discover -s tests -v
```

`config.env` is intentionally ignored and must not be committed.

## Usage rights

You are responsible for ensuring that downloading, processing, and using audio complies with the relevant platform terms and with applicable copyright and other rights.
