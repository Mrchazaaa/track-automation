"""Local yt-dlp and ffmpeg command adapters."""

import subprocess
from pathlib import Path


def download_audio(video_url, output_file):
    """Download a URL as a high-quality MP3 and return its expected path."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["yt-dlp", "--output", str(output_file.with_suffix("")), "-x", "--audio-format", "mp3", "--audio-quality", "0", video_url],
        check=True,
    )
    return output_file


def convert_to_tm2(input_file, output_file):
    """Convert an audio file to stereo 44.1 kHz PCM WAV."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_file), "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", str(output_file)],
        check=True,
    )
    return Path(output_file)


def mix_audio(input_files, output_file):
    """Mix one or more audio files into a single output track with ffmpeg."""
    input_files = [Path(input_file) for input_file in input_files]
    if not input_files:
        raise ValueError("At least one audio file is required to create a mix")

    command = ["ffmpeg", "-y"]
    for input_file in input_files:
        command.extend(["-i", str(input_file)])
    command.extend([
        "-filter_complex",
        f"amix=inputs={len(input_files)}:duration=longest",
        str(output_file),
    ])
    subprocess.run(command, check=True)
    return Path(output_file)
