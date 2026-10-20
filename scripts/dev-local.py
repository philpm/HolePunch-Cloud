#!/usr/bin/env python3
"""Start/stop an isolated local native development stack; never changes system services."""
import argparse,json,os,secrets,signal,socket,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/local-dev'
URL='http://127.0.0.1:13011'
def private(path,text):
 path.parent.mkdir(parents=True,exist_ok=True);path.parent.chmod(0o700);path.write_text(text);path.chmod(0o600)
def started(pid):
 return subprocess.run(['ps','-p',str(pid),'-o','lstart='],capture_output=True,text=True).stdout.strip()
def stop():
 if (BASE/'client/binding.json').exists():
  subprocess.run([ROOT/'vendor/holepunch/target/debug/holepunch-client','--data-dir',BASE/'client','disconnect'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
 path=BASE/'processes.json'
 if path.exists():
  for row in reversed(json.loads(path.read_text())):
   if row['started'] and started(row['pid'])==row['started']:
    os.killpg(row['pid'],signal.SIGTERM)
    for _ in range(40):
     if not started(row['pid']):break
     time.sleep(.1)
  path.unlink()
 print('Local development stack stopped. Data and credentials retained.')
def main():
 global BASE,URL
 p=argparse.ArgumentParser();p.add_argument('action',choices=['start','stop'],nargs='?',default='start');p.add_argument('--edition',choices=['cloud'],default='cloud');a=p.parse_args()
 if a.action=='stop':stop();return
 BASE.mkdir(parents=True,exist_ok=True);BASE.chmod(0o700)
 if (BASE/'processes.json').exists():raise SystemExit('Use scripts/dev-local.py stop before starting again.')
 ports=[13011,12039,12353,18463,18100,*range(25000,25021)]
 for port in ports:
  for kind in [socket.SOCK_STREAM,socket.SOCK_DGRAM]:
   with socket.socket(socket.AF_INET,kind) as probe:
    if kind==socket.SOCK_STREAM:probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    probe.bind(('127.0.0.1',port))
    if kind==socket.SOCK_STREAM:probe.listen(1)
 bins={name:ROOT/path for name,path in [('center','target/debug/holepunch-center'),('client','vendor/holepunch/target/debug/holepunch-client'),('caddy','output/tools/caddy'),('rathole','output/tools/rathole')]}
 for binary in bins.values():
  if not binary.is_file():raise SystemExit(f'Missing {binary}; see docs/DEVELOPMENT.md')
 access=BASE/'access.json'
 if not access.exists():private(access,json.dumps({'url':URL,'email':'admin@example.test','password':secrets.token_urlsafe(24),'admin_token':secrets.token_hex(32)},indent=2))
 credentials=json.loads(access.read_text());env=os.environ.copy()
 for key in ['HP_API_URL','HP_CLIENT_TOKEN','HP_LEGACY_ADMIN']:env.pop(key,None)
 env.update({'HP_ADMIN_TOKEN':credentials['admin_token'],'HP_BOOTSTRAP_EMAIL':credentials['email'],'HP_BOOTSTRAP_PASSWORD':credentials['password'],'HP_DATA_DIR':str(BASE/'data'),'HP_BIND':'127.0.0.1:13011','HP_ALLOW_HTTP':'1','HP_MAIL_OUTBOX':str(BASE/'mail'),'HP_CADDY_URL':'http://127.0.0.1:12039','HP_CADDY_LISTEN':'127.0.0.1:12039','HP_TLS_ASK_URL':URL+'/api/v1/tls/check','HP_PUBLIC_ADDR':'127.0.0.1:12353','HP_RATHOLE_BIND':'127.0.0.1:12353','HP_HTTPS_LISTEN':'127.0.0.1:18463','HP_HTTP_PORT':'18100','HP_PORT_START':'25000','HP_PORT_END':'25020','HP_PANEL_DOMAIN':'','HP_TLS_INTERNAL':'1','XDG_DATA_HOME':str(BASE/'caddy-data'),'XDG_CONFIG_HOME':str(BASE/'caddy-config'),'RUST_LOG':'info','HP_RATHOLE_BIN':str(bins['rathole'])})
 private(BASE/'caddy.json',json.dumps({'admin':{'listen':env['HP_CADDY_LISTEN']}}));rows=[]
 def launch(name,args):
  with open(BASE/(name+'.log'),'a') as log:proc=subprocess.Popen([str(bins[name]),*map(str,args)],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  rows.append({'pid':proc.pid,'started':started(proc.pid),'name':name});private(BASE/'processes.json',json.dumps(rows));return proc
 try:
  launch('caddy',['run','--config',BASE/'caddy.json']);center=launch('center',[])
  for _ in range(100):
   if center.poll() is not None:raise RuntimeError('Center exited; inspect center.log')
   if (BASE/'data/server.toml').exists():break
   time.sleep(.1)
  else:raise RuntimeError('Configuration was not generated')
  launch('rathole',['--server',BASE/'data/server.toml'])
  for _ in range(50):
   try:
    with urllib.request.urlopen(URL+'/readyz',timeout=1) as res:
     if res.status==200:break
   except OSError:pass
   time.sleep(.2)
  else:raise RuntimeError('Local edge readiness timed out; inspect logs')
  if (BASE/'client/binding.json').exists():launch('client',['--data-dir',BASE/'client','connect'])
  private(BASE/'ACCESS.md',f'# Local development access\n\nPanel: {URL}\n\nEmail: `{credentials["email"]}`\n\nPassword: `{credentials["password"]}`\n\nLocal development only. Never commit or share this file. A password changed in the console invalidates this initial password.\n\nUse Language in the page header. Open Setup guide for server configuration, Default policy for registration and limits, and User management for individual limits. Development mail is stored in `mail/`; it is not sent externally.\n\nStop: `python3 scripts/dev-local.py stop`. Data is retained.\n')
  print(f'Local panel: {URL}\nCredentials: {BASE/"ACCESS.md"}')
 except BaseException:
  stop();raise
if __name__=='__main__':main()
