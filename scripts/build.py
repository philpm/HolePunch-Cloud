#!/usr/bin/env python3
"""Build the Cloud server and pinned shared CLI without changing the submodule revision."""
import argparse,shutil,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--release',action='store_true');a=p.parse_args()
flags=['--release'] if a.release else []
subprocess.run(['cargo','build','--workspace','--locked',*flags],cwd=r,check=True)
subprocess.run(['cargo','build','--manifest-path',str(r/'vendor/holepunch/Cargo.toml'),'--locked','-p','holepunch-cli',*flags],cwd=r,check=True)
profile='release' if a.release else 'debug'
ext='.exe' if __import__('os').name=='nt' else ''
shutil.copy2(r/'vendor/holepunch/target'/profile/('holepunch-client'+ext),r/'target'/profile/('holepunch-client'+ext))
