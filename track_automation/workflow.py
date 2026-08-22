"""Application workflow for sequential stem separation."""

import os
from pathlib import Path

from .lalal_client import LalalAI
from .media import mix_audio


SUPPORTED_AUDIO_SUFFIXES = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
INSTRUMENT_ALIASES = {
    "drums": "drum",
    "drum": "drum",
    "voice": "vocals",
    "voices": "vocals",
    "vocal": "vocals",
    "vocals": "vocals",
    "guitar": "guitar",
    "bass": "bass",
    "piano": "piano",
}


def normalise_instruments(instruments):
    """Map user-friendly names to the LALAL.AI stem identifiers."""
    normalised = []
    for instrument in instruments:
        key = instrument.lower().strip()
        if key not in INSTRUMENT_ALIASES:
            choices = ", ".join(sorted(INSTRUMENT_ALIASES))
            raise ValueError(f"Unsupported instrument '{instrument}'. Choose from: {choices}")
        stem = INSTRUMENT_ALIASES[key]
        if stem not in normalised:
            normalised.append(stem)
    return normalised


def split_instr(input_file_path, api_key, output_dir, stem, back_filename_descr):
    """Separate one stem and download both the stem and backing track."""
    input_file = Path(input_file_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    if input_file.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
        print("⚠️  Warning: Input file should be an audio file (mp3, wav, flac, ogg, m4a)")

    api_key = api_key or os.getenv("LALAL_API_KEY")
    if not api_key:
        raise ValueError("API key required. Set LALAL_API_KEY or use --api-key")

    output_dir = Path(output_dir) if output_dir else input_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    client = LalalAI(api_key)
    print("🔍 Checking account limits...")
    limits = client.check_limits()
    print(f"💰 Account: {limits.get('option', 'Unknown')}")
    print(f"📧 Email: {limits.get('email', 'Unknown')}")
    print(f"⏱️  Duration left: {limits.get('process_duration_left', 0):.1f} minutes")

    print(f"\n📤 Uploading: {input_file.name}")
    upload = client.upload_file(str(input_file))
    file_id = upload["id"]
    print(f"✓ File uploaded successfully. ID: {file_id}")
    print(f"\n🎵 Starting stem separation for: {stem}")
    client.split_audio(file_id, stem)
    split = client.wait_for_completion(file_id)

    stem_path = back_path = None
    print(f"\n⬇️  Downloading results to: {output_dir}")
    if split.get("stem_track"):
        stem_path = output_dir / f"{input_file.stem}_{split.get('stem', 'stem')}{input_file.suffix}"
        client.download_file(split["stem_track"], str(stem_path))
    if split.get("back_track"):
        back_path = output_dir / f"{back_filename_descr}{input_file.suffix}"
        client.download_file(split["back_track"], str(back_path))
    return {"stem_track": stem_path, "back_track": back_path}


def separate_drums_and_vocals(input_file_path, api_key=None, output_dir=None):
    """Create a drum-free, then vocal-and-drum-free, backing track."""
    input_file = Path(input_file_path)
    drums = split_instr(input_file, api_key, output_dir, "drum", f"{input_file.stem}_no_drums")
    return split_instr(
        drums["back_track"],
        api_key,
        output_dir,
        "vocals",
        f"{input_file.stem}_no_drums_no_vocals",
    )


def create_instrument_mix(input_file_path, instruments, api_key=None, output_dir=None):
    """Extract requested stems and mix them into one output track."""
    input_file = Path(input_file_path)
    output_dir = Path(output_dir) if output_dir else input_file.parent
    stems = normalise_instruments(instruments)
    if not stems:
        raise ValueError("Specify at least one instrument")

    stem_tracks = []
    for stem in stems:
        result = split_instr(input_file, api_key, output_dir, stem, f"{input_file.stem}_without_{stem}")
        if result["stem_track"] is None:
            raise RuntimeError(f"LALAL.AI did not return a {stem} track")
        stem_tracks.append(result["stem_track"])

    output = output_dir / f"{input_file.stem}_{'_'.join(stems)}{input_file.suffix}"
    return mix_audio(stem_tracks, output)
