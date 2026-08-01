#!/bin/bash
# Run VivisectION unit tests with headless Qt (offscreen platform)
export QT_QPA_PLATFORM=offscreen
cd "$(dirname "$0")/.."
python3 -m pytest tests/ -v "$@"