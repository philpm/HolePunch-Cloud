#!/usr/bin/env python3
"""macOS-only local package/service smoke. Requires scripts/dev-local.py start.
Uses a temporary HOME and refuses to touch an existing dev.holepunch.cli service.
"""
import argparse,platform,sys,contextlib,hashlib,http.cookiejar,json,os,socket,socketserver,subprocess,tarfile,tempfile,threading,time,urllib.request
from pathlib import Path
if sys.platform!='darwin':raise SystemExit('This service smoke is macOS-only')
uid=subprocess.check_output(['id','-u'],text=True).strip();target=f'gui/{uid}/dev.holepunch.cli'
assert subprocess.run(['launchctl','print',target],capture_output=True).returncode!=0,'Existing user service: refusing to interfere'
root=Path(__file__).resolve().parents[1];run=Path(tempfile.mkdtemp(prefix='cli service ',dir=root/'output'));run.chmod(0o700)
parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path);args=parser.parse_args()
metadata=json.loads(subprocess.check_output(['cargo','metadata','--locked','--no-deps','--format-version','1'],cwd=root/'vendor/holepunch'))
version=next(p['version'] for p in metadata['packages'] if p['name']=='holepunch-cli')
arch='aarch64' if platform.machine()=='arm64' else 'x86_64'
archive=args.archive or root/'vendor/holepunch'/f'dist/holepunch-selfhost-{version}-{arch}-apple-darwin.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==archive.with_name(archive.name+'.sha256').read_text().split()[0]
with tarfile.open(archive) as t:t.extractall(run)
bin_dir=next(run.glob('holepunch-*/bin'));cli=bin_dir/'holepunch-client';assert version in subprocess.check_output([cli,'--version'],text=True)
access=json.load(open(root/'output/local-dev/access.json'));http=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
csrf=''
def api(path,method='GET',body=None):
 req=urllib.request.Request(access['url']+'/api/v1'+path,method=method,headers={'Content-Type':'application/json','X-CSRF-Token':csrf},data=None if body is None else json.dumps(body).encode())
 with http.open(req,timeout=10) as r:return json.load(r)
csrf=api('/auth/login','POST',{'email':access['email'],'password':access['password']})['csrf']
class Echo(socketserver.BaseRequestHandler):
 def handle(self):
  with contextlib.suppress(OSError):
   while data:=self.request.recv(4096):self.request.sendall(data)
class Server(socketserver.ThreadingTCPServer):allow_reuse_address=True;daemon_threads=True
server=Server(('127.0.0.1',19212),Echo);threading.Thread(target=server.serve_forever,daemon=True).start()
env=os.environ.copy()
for key in ['HP_API_URL','HP_CLIENT_TOKEN']:env.pop(key,None)
env.update({'HOME':str(run/'home'),'HP_CLIENT_DATA':str(run/'client'),'HP_RATHOLE_BIN':str(bin_dir/'rathole')})
def command(*args):return subprocess.run([cli,*args],env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).stdout
def wait(fn):
 for _ in range(120):
  try:
   if fn():return
  except (OSError,ValueError):pass
  time.sleep(.25)
 raise AssertionError('timeout')
proc=None;device=None
try:
 device=api('/portal/clients','POST',{'name':'cli-service-smoke'})
 tunnel=api('/portal/tunnels','POST',{'name':'cli-service-smoke','client_id':device['id'],'protocol':'tcp','local_host':'127.0.0.1','local_port':19212,'enabled':True,'bandwidth_limit_bps':128000})
 with open(run/'cli.log','w') as log:
  proc=subprocess.Popen([cli,'connect','--server',access['url'],'--token-stdin'],env=env,stdin=subprocess.PIPE,stdout=log,stderr=log)
  proc.stdin.write((device['enroll_token']+'\n').encode());proc.stdin.close()
  wait(lambda:(run/'client/status.json').exists())
  before=(run/'client/client.toml').read_bytes();assert 'passed' in command('doctor');assert before==(run/'client/client.toml').read_bytes()
  command('disconnect');proc.wait(timeout=10);assert (run/'client/binding.json').exists()
 command('service','install');command('service','install');command('service','start')
 wait(lambda:json.loads((run/'client/status.json').read_text())['running'])
 def echo_ready():
  with socket.create_connection(('127.0.0.1',tunnel['public_port']),timeout=5) as s:s.sendall(b'service');return s.recv(7)==b'service'
 wait(echo_ready)
 command('service','start');command('service','stop');command('service','stop');command('service','uninstall');command('service','uninstall');command('logout')
 assert not (run/'client/binding.json').exists()
 print('PASS archive checksum/version, package paths with spaces, enrollment, read-only doctor, disconnect, macOS service install/start/echo/stop/uninstall (repeated), logout')
finally:
 with contextlib.suppress(Exception):command('service','stop');command('service','uninstall')
 if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=10)
 if device:api('/portal/clients/'+device['id']+'/revoke','POST',{})
 api('/auth/logout','POST',{})
 server.shutdown();server.server_close()
