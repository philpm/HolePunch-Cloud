#!/usr/bin/env python3
"""Generate private, interactive Cloud Compose settings."""
from _shared import load, ROOT, SCRIPT_DIR

setup = load('setup')
setup.ROOT = ROOT
setup.SCRIPT_DIR = SCRIPT_DIR
if __name__ == '__main__':
    setup.main(edition='cloud')
