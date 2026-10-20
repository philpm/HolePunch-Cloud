#!/usr/bin/env python3
"""Start Cloud Compose and show initial browser access after readiness."""
import sys
from _shared import load, ROOT

compose = load('compose')
compose.ROOT = ROOT
compose.DEFAULT_COMPOSE = ROOT / ('docker-compose.yml' if (ROOT / 'docker-compose.yml').exists() else 'compose.release.yml')
if __name__ == '__main__':
    sys.exit(compose.main())
