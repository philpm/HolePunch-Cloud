"""Cloud deployment composition, product boundaries and standalone release loading."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('cloud_install', ROOT / 'scripts/deploy.py')
cloud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloud)


class DeploymentTests(unittest.TestCase):
    def test_published_release_checks_cloud_url_checksum_and_metadata(self):
        import hashlib
        import zipfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = '0.4.0-dev.1'
            target = cloud.deploy.target()
            extension = '.zip' if os.name == 'nt' else '.tar.gz'
            name = f'holepunch-cloud-{version}-{target}{extension}'
            stage = root / 'package'
            stage.mkdir()
            archive = root / name
            build = {'edition': 'cloud', 'target': target, 'version': version}

            def make_archive(metadata):
                (stage / 'BUILD.json').write_text(json.dumps(metadata))
                if extension == '.zip':
                    with zipfile.ZipFile(archive, 'w') as bundle:
                        bundle.write(stage / 'BUILD.json', 'package/BUILD.json')
                else:
                    with tarfile.open(archive, 'w:gz') as bundle:
                        bundle.add(stage, arcname='package')
                archive.with_name(name + '.sha256').write_text(
                    hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + name + '\n'
                )

            urls = []

            def download(url, destination):
                urls.append(url)
                shutil.copyfile(root / url.rsplit('/', 1)[1], destination)

            args = SimpleNamespace(version='v' + version, source=None, archive=None, checksum=None)
            with mock.patch.object(cloud.deploy, 'download', side_effect=download):
                make_archive(build)
                work = root / 'valid'
                work.mkdir()
                binaries = cloud.native_binaries(args, work)
                self.assertEqual(set(binaries), {'holepunch-center', 'holepunch-client', 'rathole'})
                base = f'https://github.com/philpm/HolePunch-Cloud/releases/download/v{version}/'
                self.assertEqual(urls, [base + name, base + name + '.sha256'])

                for field, wrong in [('edition', 'selfhost'), ('target', 'wrong-target'), ('version', '0.0.0')]:
                    with self.subTest(field=field):
                        make_archive({**build, field: wrong})
                        work = root / field
                        work.mkdir()
                        with self.assertRaises(ValueError):
                            cloud.native_binaries(args, work)

                make_archive(build)
                archive.write_bytes(b'corrupted archive')
                work = root / 'corrupt'
                work.mkdir()
                with self.assertRaisesRegex(ValueError, 'SHA256 verification failed'):
                    cloud.native_binaries(args, work)

    def test_compose_bootstrap_is_cloud_private_and_non_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            command = [sys.executable, str(ROOT / 'scripts/setup.py'), '--public-host', 'edge.example.test', '--output', str(path)]
            subprocess.run(command, check=True, capture_output=True)
            values = dict(line.split('=', 1) for line in path.read_text().splitlines())
            self.assertEqual(values['HP_EDITION'], 'cloud')
            self.assertGreaterEqual(len(values['HP_BOOTSTRAP_PASSWORD']), 24)
            self.assertTrue(path.with_name('.env.access.txt').exists())
            if os.name != 'nt':
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            original = path.read_bytes()
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(path.read_bytes(), original)

    def test_archive_edition_is_enforced(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / 'package'
            stage.mkdir()
            for edition in ['selfhost', 'cloud']:
                (stage / 'BUILD.json').write_text(json.dumps({'edition': edition, 'target': cloud.deploy.target()}))
                archive = root / (edition + '.tar.gz')
                with tarfile.open(archive, 'w:gz') as tar:
                    tar.add(stage, arcname='package')
                archive.with_name(archive.name + '.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n')
                args = SimpleNamespace(version=None, source=None, archive=archive, checksum=None)
                work = root / edition
                work.mkdir()
                if edition == 'selfhost':
                    with self.assertRaisesRegex(ValueError, 'edition'):
                        cloud.native_binaries(args, work)
                else:
                    self.assertEqual(set(cloud.native_binaries(args, work)), {'holepunch-center', 'holepunch-client', 'rathole'})

    def test_standalone_release_uses_packaged_shared_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['_shared.py', 'deploy.py', 'setup.py', 'compose.py', 'access.py']:
                shutil.copyfile(ROOT / 'scripts' / name, root / name)
            (root / 'shared').mkdir()
            for name in ['deploy.py', 'setup.py', 'compose.py', 'access.py']:
                shutil.copyfile(ROOT / 'vendor/holepunch/scripts' / name, root / 'shared' / name)
            # Release archives also carry core documentation, without its source scripts.
            (root / 'vendor/holepunch/docs').mkdir(parents=True)
            command = [sys.executable, str(root / 'setup.py'), '--public-host', 'edge.example.test']
            subprocess.run(command, cwd=root, check=True, capture_output=True)
            self.assertIn('HP_EDITION=cloud', (root / '.env').read_text())
            subprocess.run([sys.executable, str(root / 'deploy.py'), '--help'], cwd=root, check=True, capture_output=True)
            result = subprocess.run([sys.executable, str(root / 'access.py'), '--env-file', str(root / '.env'), '--hide-secrets'], cwd=root, check=True, capture_output=True, text=True)
            self.assertIn('Management URL:', result.stdout)
            self.assertIn('[hidden;', result.stdout)

    def test_cloud_diagnostics_are_localized(self):
        import re
        source = (ROOT / 'apps/cloud/src/lib.rs').read_text()
        catalog = json.loads((ROOT / 'vendor/holepunch/web/locales/en.json').read_text())
        messages = re.findall(r'bad\("([^"]+)"\)|StatusCode::[A-Z_]+,\s*"([^"]+)"', source)
        for pair in messages:
            self.assertIn(next(value for value in pair if value), catalog)


if __name__ == '__main__':
    unittest.main()
