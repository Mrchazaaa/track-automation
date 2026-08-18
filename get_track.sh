#!/bin/bash

# Check if a string argument was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <string>"
  exit 1
fi

VIDEO_URL="$1"
FILENAME="$2"

source ./config.env

mkdir -p ./tracks
mkdir ./tracks/$FILENAME

echo "Downloading video URL: $VIDEO_URL"
yt-dlp --output "./tracks/$FILENAME/$FILENAME" -x --audio-format mp3 --audio-quality 0 $VIDEO_URL
echo "Video downloaded"

echo "Separating stems"
python3 ./TrackSeparation.py --input-file "./tracks/$FILENAME/$FILENAME.mp3" --api-key $LALAL_API_KEY --output-dir "./tracks/$FILENAME"
echo "Stems separated"

echo "Converting to TM2 format"
ffmpeg -i "./tracks/$FILENAME/${FILENAME}_no_drums_no_vocals.mp3" -acodec pcm_s16le -ar 44100 -ac 2 "./tracks/$FILENAME/${FILENAME}_no_drums_no_vocals_tm2ready.wav"
echo "Conversion complete"