#!/bin/sh
# Run from an Cloud checkout or downloaded release archive.
set -eu
exec python3 "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/deploy.py" install "$@"
