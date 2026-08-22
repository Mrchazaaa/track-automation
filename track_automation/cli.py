"""Command-line interface for track automation."""

import argparse
from pathlib import Path

from .media import convert_to_tm2, download_audio
from .workflow import create_instrument_mix


def build_parser():
    parser = argparse.ArgumentParser(description="Download audio and create a selected-instrument track")
    parser.add_argument("video_url", nargs="?", help="Video URL to download")
    parser.add_argument("name", nargs="?", help="Output track name")
    parser.add_argument("--input-file", help="Use an existing audio file instead of downloading")
    parser.add_argument("--api-key", help="LALAL.AI API key (or set LALAL_API_KEY)")
    parser.add_argument("--output-dir", help="Output directory for an existing input file")
    parser.add_argument(
        "--include",
        nargs="+",
        metavar="INSTRUMENT",
        required=True,
        help="Instruments to include, e.g. --include drums voice guitar",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.input_file:
        create_instrument_mix(args.input_file, args.include, args.api_key, args.output_dir)
        return
    if not args.video_url or not args.name:
        build_parser().error("video_url and name are required unless --input-file is provided")

    output_dir = Path("tracks") / args.name
    source = download_audio(args.video_url, output_dir / f"{args.name}.mp3")
    selected_track = create_instrument_mix(source, args.include, args.api_key, output_dir)
    convert_to_tm2(selected_track, output_dir / f"{args.name}_selected_tm2ready.wav")


if __name__ == "__main__":
    main()
