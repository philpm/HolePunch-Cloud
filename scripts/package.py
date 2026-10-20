#!/usr/bin/env python3
"""Package Cloud using the pinned public packaging implementation."""
import argparse, importlib.util, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'vendor/holepunch'
# Reuse the public packager while overriding only product-specific inputs.
spec=importlib.util.spec_from_file_location('holepunch_packager',CORE/'scripts/package.py')
packager=importlib.util.module_from_spec(spec);spec.loader.exec_module(packager)
packager.ROOT=ROOT
packager.version=lambda:json.loads(subprocess.check_output(['cargo','metadata','--no-deps','--locked','--format-version','1'],cwd=ROOT))['packages'][0]['version']
# Cloud packaging is implemented through an explicit public extension entry point.
extra = {script: ROOT/'scripts'/script for script in ['_shared.py', 'deploy.py', 'setup.py', 'compose.py', 'access.py', 'install.sh', 'install.ps1']}
extra.update({'shared/'+script: CORE/'scripts'/script for script in ['deploy.py', 'setup.py', 'compose.py', 'access.py']})
extra['compose.release.yml'] = ROOT/'deploy/compose.release.yml'
packager.main(edition='cloud', shared_root=CORE, extra_files=extra)
