#!/usr/bin/env python3
"""Install Cloud from source or a checksum-verified release archive."""
import os
import subprocess
import sys
from _shared import load

deploy = load('deploy')
deploy.EDITION = 'cloud'
deploy.REPOSITORY = 'philpm/HolePunch-Cloud'
shared_binaries = deploy.native_binaries


def native_binaries(args, work):
    if not args.source:
        return shared_binaries(args, work)
    source = args.source.resolve()
    core = source / 'vendor/holepunch'
    if not (source / 'apps/cloud/Cargo.toml').is_file() or not (core / 'Cargo.toml').is_file():
        raise ValueError('Use a Cloud checkout with its pinned core submodule initialized')
    subprocess.run([sys.executable, str(source / 'scripts/build.py'), '--release'], cwd=source, check=True)
    subprocess.run([sys.executable, str(core / 'scripts/build-rathole.py')], cwd=core, check=True)
    ext = '.exe' if os.name == 'nt' else ''
    return {
        'holepunch-center': source / 'target/release' / ('holepunch-cloud' + ext),
        'holepunch-client': source / 'target/release' / ('holepunch-client' + ext),
        'rathole': core / 'apps/desktop/src-tauri/binaries' / ('holepunch-rathole-' + deploy.target() + ext),
    }


deploy.native_binaries = native_binaries
if __name__ == '__main__':
    sys.exit(deploy.main())
