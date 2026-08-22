#!/bin/bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <video-url> <track-name>" >&2
  exit 1
fi

set -a
source ./config.env
set +a
python3 -m track_automation.cli "$1" "$2" --include vocals drums
