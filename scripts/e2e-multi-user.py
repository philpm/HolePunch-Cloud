#!/usr/bin/env python3
"""Isolated local multi-user + CLI + per-tunnel bandwidth acceptance.
Uses Caddy internal CA; never contacts production or modifies system trust.
"""
import base64,hashlib,argparse,contextlib,http.cookiejar,json,os,secrets,socket,socketserver,ssl,subprocess,tempfile,threading,time,urllib.request,urllib.error
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--caddy',required=True);p.add_argument('--rathole',required=True);p.add_argument('--rate-seconds',type=int,default=0);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=root/'output/multi-user';out.mkdir(parents=True,exist_ok=True);run=Path(tempfile.mkdtemp(dir=out));run.chmod(0o700)
BASE='http://127.0.0.1:13010';processes=[];handles=[];servers=[];checks=[]
def launch(cmd,name,env=None,stdin=None):
 log=open(run/(name+'.log'),'w');handles.append(log);proc=subprocess.Popen([str(x) for x in cmd],env=env,cwd=root,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.PIPE if stdin else subprocess.DEVNULL);processes.append(proc)
 if stdin:proc.stdin.write((stdin+'\n').encode());proc.stdin.close()
 return proc
class Session:
 def __init__(self):self.jar=http.cookiejar.CookieJar();self.http=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar));self.csrf=''
 def call(self,path,method='GET',data=None):
  req=urllib.request.Request(BASE+'/api/v1'+path,method=method,headers={'Content-Type':'application/json','X-CSRF-Token':self.csrf},data=None if data is None else json.dumps(data).encode())
  try:
   with self.http.open(req,timeout=10) as r:raw=r.read();v=json.loads(raw) if raw else {};return r.status,v
  except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
 def ok(self,path,method='GET',data=None):
  code,v=self.call(path,method,data);assert code==200,(path,code,v);return v
 def login(self,email,password):self.csrf=self.ok('/auth/login','POST',{'email':email,'password':password})['csrf']
def wait(fn,label,timeout=30):
 end=time.monotonic()+timeout;last=None
 while time.monotonic()<end:
  try:
   v=fn()
   if v:return v
  except Exception as e:last=type(e).__name__
  time.sleep(.25)
 raise AssertionError(label+' timeout '+str(last))
def passed(label):checks.append(label);print('PASS',label,flush=True)
class TCP(socketserver.BaseRequestHandler):
 def handle(self):
  with contextlib.suppress(OSError):
   while data:=self.request.recv(4096):self.request.sendall(data)
class UDP(socketserver.BaseRequestHandler):
 def handle(self):self.request[1].sendto(self.request[0],self.client_address)
class HTTP(socketserver.BaseRequestHandler):
 def handle(self):
  data=self.request.recv(8192)
  if b'Upgrade: websocket' not in data:
   self.request.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 12\r\nConnection: close\r\n\r\nfood-api-dev');return
  key=data.split(b'Sec-WebSocket-Key: ')[1].split(b'\r\n')[0]
  accept=base64.b64encode(hashlib.sha1(key+b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
  self.request.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+b'\r\n\r\n')
  with contextlib.suppress(OSError):
   while frame:=self.request.recv(131):
    if len(frame)<6:return
    n=frame[1]&127;mask=frame[2:6];payload=bytes(b^mask[i%4] for i,b in enumerate(frame[6:6+n]))
    self.request.sendall(bytes([0x81,len(payload)])+payload)
class TS(socketserver.ThreadingTCPServer):allow_reuse_address=True;daemon_threads=True
class US(socketserver.ThreadingUDPServer):allow_reuse_address=True;daemon_threads=True
def echo(port,n=32,udp=False):
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM if udp else socket.SOCK_STREAM) as s:
  s.settimeout(12);s.connect(('127.0.0.1',port));data=b'a'*n;s.sendall(data);received=b''
  while len(received)<n:received+=s.recv(n-len(received))
  return received==data
def closed(port):
 try:
  with socket.create_connection(('127.0.0.1',port),timeout=.5):return False
 except OSError:return True
def code_from_mail(address,purpose):
 for f in sorted((run/'mail').glob('*.txt'),key=lambda f:f.stat().st_mtime,reverse=True):
  s=f.read_text()
  if address in s and 'HolePunch '+purpose in s:return s.split('One-time code (valid for 30 minutes): ')[1].splitlines()[0]
 raise AssertionError('mail missing')
try:
 # Fail early on occupied ports, including specific-loopback listeners that can
 # coexist with wildcard listeners on macOS.
 for port in [13010,12029,12343,18453,18090,19201,19202,19203,*range(24000,24021),30000,30001]:
  for kind in [socket.SOCK_STREAM,socket.SOCK_DGRAM]:
   with socket.socket(socket.AF_INET,kind) as probe:
    if kind==socket.SOCK_STREAM:probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    probe.bind(('127.0.0.1',port))
    if kind==socket.SOCK_STREAM:probe.listen(1)
 for cls,handler,port in [(TS,TCP,19201),(US,UDP,19202),(TS,HTTP,19203)]:
  server=cls(('127.0.0.1',port),handler);servers.append(server);threading.Thread(target=server.serve_forever,daemon=True).start()
 env=os.environ.copy();password=secrets.token_urlsafe(24)
 env.update({'RUST_LOG':'info,holepunch_server_core::bandwidth=debug','HP_ADMIN_TOKEN':secrets.token_hex(32),'HP_DATA_DIR':str(run/'center'),'HP_BIND':'127.0.0.1:13010','HP_BOOTSTRAP_EMAIL':'admin@example.test','HP_BOOTSTRAP_PASSWORD':password,'HP_ALLOW_HTTP':'1','HP_MAIL_OUTBOX':str(run/'mail'),'HP_CADDY_URL':'http://127.0.0.1:12029','HP_CADDY_LISTEN':'127.0.0.1:12029','HP_TLS_ASK_URL':BASE+'/api/v1/tls/check','HP_PUBLIC_ADDR':'127.0.0.1:12343','HP_RATHOLE_BIND':'127.0.0.1:12343','HP_HTTPS_LISTEN':'127.0.0.1:18453','HP_HTTP_PORT':'18090','HP_PORT_START':'24000','HP_PORT_END':'24020','HP_PANEL_DOMAIN':'','HP_TLS_INTERNAL':'1'})
 config=run/'caddy.json';config.write_text(json.dumps({'admin':{'listen':'127.0.0.1:12029'}}));env['XDG_DATA_HOME']=str(run/'caddy-data');env['XDG_CONFIG_HOME']=str(run/'caddy-config')
 launch([a.caddy,'run','--config',config],'caddy',env);center=launch([root/'target/debug/holepunch-center'],'center',env)
 admin=Session();wait(lambda:admin.call('/auth/login','POST',{'email':'admin@example.test','password':password})[0]==200,'bootstrap login');admin.login('admin@example.test',password);passed('Explicit administrator bootstrap and password session')
 admin.ok('/admin/policy','PUT',{'clients':1,'tunnels':2,'bps':1000000,'registration':True,'domain_suffix':'t.example.test'})
 user=Session();user.ok('/auth/register','POST',{'email':'alice@example.test','password':password});user.login('alice@example.test',password)
 assert user.call('/portal/clients','POST',{'name':'blocked'})[0]==403;passed('Unverified email cannot create devices')
 token=code_from_mail('alice@example.test','verify');user.ok('/auth/verify','POST',{'token':token});assert user.call('/auth/verify','POST',{'token':token})[0]==400;passed('Email verification and one-time challenge')
 device=user.ok('/portal/clients','POST',{'name':'local-cli'});assert user.call('/portal/clients','POST',{'name':'second'})[0]==409;passed('Default single-device quota')
 sync=lambda:admin.ok('/sync','POST',{})
 wait(lambda:(run/'center/server.toml').exists(),'server config');launch([a.rathole,'--server',run/'center/server.toml'],'rathole',env)
 client_env=os.environ.copy();client_env.update({'HP_CLIENT_DATA':str(run/'client'),'HP_RATHOLE_BIN':str(Path(a.rathole).resolve()),'RUST_LOG':'info,holepunch_server_core::bandwidth=debug'})
 client=launch([root/'vendor/holepunch/target/debug/holepunch-client','connect','--server',BASE,'--token-stdin'],'client',client_env,device['enroll_token'])
 wait(lambda:(run/'client/status.json').exists(),'CLI status');assert user.call('/enroll','POST',{'token':device['enroll_token']})[0]==400;passed('Single-use CLI enrollment without hand-written config')
 def new(protocol,local,bps=128000):return {'name':'food-'+protocol,'client_id':device['id'],'protocol':protocol,'local_host':'127.0.0.1','local_port':local,'enabled':True,'bandwidth_limit_bps':bps}
 tcp=user.ok('/portal/tunnels','POST',new('tcp',19201));udp=user.ok('/portal/tunnels','POST',new('udp',19202));sync()
 wait(lambda:echo(tcp['public_port']),'first tunnel after empty client');passed('Web-created first tunnel hot-syncs into running CLI')
 wait(lambda:echo(udp['public_port'],udp=True),'UDP');passed('UDP through server-owned gateway and Noise')
 assert user.call('/portal/tunnels','POST',new('tcp',19201))[0]==409;passed('Default two-tunnel quota')
 # Aggregate two concurrent connections through the same tunnel: 64 KB / 16 KB/s.
 start=time.monotonic();result=[]
 threads=[threading.Thread(target=lambda:result.append(echo(tcp['public_port'],16000))) for _ in range(2)]
 for t in threads:t.start()
 for t in threads:t.join()
 elapsed=time.monotonic()-start;assert result==[True,True] and 3.8<=elapsed<=8,elapsed;passed('Per-tunnel shared bidirectional rate across concurrent connections')
 rate_report={}
 if a.rate_seconds:
  user.ok('/portal/bandwidth','POST',{'allocations':[{'tunnel_id':tcp['id'],'bps':600000},{'tunnel_id':udp['id'],'bps':400000}]});sync()
  wait(lambda:echo(tcp['public_port']),'TCP rate ready');wait(lambda:echo(udp['public_port'],udp=True),'UDP rate ready')
  counts={'tcp':0,'udp':0};errors=[];guard=threading.Lock();barrier=threading.Barrier(5);samples=[]
  def stream(kind,port):
   try:
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM if kind=='udp' else socket.SOCK_STREAM) as peer:
     peer.settimeout(10);peer.connect(('127.0.0.1',port));barrier.wait();deadline=time.monotonic()+a.rate_seconds;data=b'r'*(1000 if kind=='udp' else 4000)
     while time.monotonic()<deadline:
      peer.sendall(data);received=b''
      while len(received)<len(data):
       piece=peer.recv(len(data)-len(received))
       if not piece:raise AssertionError('rate stream closed')
       received+=piece
      assert received==data
      with guard:counts[kind]+=len(data)*2
   except Exception as e:errors.append(str(e))
  flows=[threading.Thread(target=stream,args=(kind,t['public_port'])) for kind,t in [('tcp',tcp),('udp',udp)] for _ in range(2)]
  for flow in flows:flow.start()
  start=time.monotonic();barrier.wait()
  while any(f.is_alive() for f in flows):
   samples.append(subprocess.check_output(['ps','-p',str(center.pid),'-o','%cpu=,rss='],text=True).strip());time.sleep(1)
  duration=time.monotonic()-start;assert not errors,errors
  for kind,budget in [('tcp',600000),('udp',400000)]:
   bps=counts[kind]*8/duration;assert budget*.85<=bps<=budget*1.05,(kind,bps,budget)
   rate_report[kind]={'bps':round(bps),'budget_bps':budget}
  rate_report.update({'seconds':round(duration,2),'center_cpu_rss_samples':samples})
  passed('60-second TCP/UDP independent 0.6/0.4 Mbps caps, multi-flow utilization and CPU/RSS sampling')
  user.ok('/portal/bandwidth','POST',{'allocations':[{'tunnel_id':tcp['id'],'bps':128000},{'tunnel_id':udp['id'],'bps':128000}]});sync()
 # Reducing TCP limit applies to existing/new traffic by closing changed gateway.
 change=new('tcp',19201,64000);user.ok('/portal/tunnels/'+tcp['id'],'PUT',change);sync();wait(lambda:echo(tcp['public_port']),'TCP after hot decrease')
 start=time.monotonic();assert echo(tcp['public_port'],8000);assert time.monotonic()-start>=1.9;passed('Hot bandwidth decrease without client restart')
 # Disabled tunnels keep their allocations; zero disables.
 change['enabled']=False;user.ok('/portal/tunnels/'+tcp['id'],'PUT',change);sync();wait(lambda:closed(tcp['public_port']),'disabled public port');assert user.ok('/me')['allocated_bps']==192000;passed('Disabled tunnel retains allocation and closes public port')
 user.ok('/portal/tunnels/'+tcp['id'],'DELETE');assert user.ok('/me')['allocated_bps']==128000;passed('Deleting tunnel releases assigned bandwidth')
 web=user.ok('/portal/tunnels','POST',new('web',19203,600000));assert web['domain'].endswith('.t.example.test');sync()
 def https():
  with socket.create_connection(('127.0.0.1',18453),timeout=5) as sock:
   with ssl._create_unverified_context().wrap_socket(sock,server_hostname=web['domain']) as tls:
    tls.sendall(('GET / HTTP/1.1\r\nHost: '+web['domain']+'\r\nConnection: close\r\n\r\n').encode());data=b''
    while chunk:=tls.recv(4096):data+=chunk
    return b'food-api-dev' in data
 wait(https,'HTTPS');passed('Random platform domain HTTPS reaches local HTTP through limited gateway')
 ws=ssl._create_unverified_context().wrap_socket(socket.create_connection(('127.0.0.1',18453),timeout=5),server_hostname=web['domain']);ws.settimeout(5)
 ws.sendall(('GET /ws HTTP/1.1\r\nHost: '+web['domain']+'\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n').encode())
 assert b'101' in ws.recv(4096);ws.sendall(b'\x81\x84mask'+bytes(c^b'mask'[i%4] for i,c in enumerate(b'food')));assert ws.recv(1024)==b'\x81\x04food';passed('WebSocket upgrade and bidirectional messages traverse limited tunnel')
 # Freeze must cut server traffic and reject device API even for old clients.
 me=user.ok('/me');uid=me['user']['id'];admin.ok('/admin/users/'+uid,'PUT',{'status':'frozen','role':'user','clients':None,'tunnels':None,'bps':None});sync();wait(lambda:closed(web['public_port']),'freeze');assert user.call('/me')[0]==401;passed('User freeze revokes sessions and removes server data routes')
 assert ws.recv(1024)==b'';ws.close();passed('Freeze terminates an already active WebSocket connection')
 binding=json.loads((run/'client/binding.json').read_text());req=urllib.request.Request(BASE+'/api/v1/client/config',headers={'Authorization':'Bearer '+binding['token']})
 try:urllib.request.urlopen(req);raise AssertionError('frozen device admitted')
 except urllib.error.HTTPError as e:assert e.code==403
 passed('Frozen account invalidates existing device credentials')
 wait(lambda:not json.loads((run/'client/status.json').read_text())['running'],'CLI suspends frozen account');assert (run/'client/binding.json').exists()
 admin.ok('/admin/users/'+uid,'PUT',{'status':'active','role':'user','clients':None,'tunnels':None,'bps':None});user.login('alice@example.test',password)
 sync();wait(https,'CLI automatically recovers after unfreeze');passed('Unfreeze automatically resumes CLI without re-enrollment')
 subprocess.run([str(root/'vendor/holepunch/target/debug/holepunch-client'),'disconnect'],env=client_env,check=True,stdout=subprocess.DEVNULL);client.wait(timeout=10);passed('CLI disconnect reaps process and retains binding')
 # Password reset invalidates previous browser session and rejects token replay.
 user.ok('/auth/request-reset','POST',{'email':'alice@example.test'});reset=code_from_mail('alice@example.test','reset');new_password=secrets.token_urlsafe(24);user.ok('/auth/reset','POST',{'token':reset,'password':new_password});assert user.call('/me')[0]==401;assert user.call('/auth/reset','POST',{'token':reset,'password':new_password})[0]==400;user.login('alice@example.test',new_password);passed('Password reset invalidates sessions and cannot replay')
 user.ok('/portal/clients/'+device['id']+'/revoke','POST',{});assert user.ok('/me')['allocated_bps']==0;sync();passed('Device revocation deletes owned tunnels and releases allocation')
 invited=admin.ok('/admin/users','POST',{'email':'bob@example.test'});bob=Session();bob_password=secrets.token_urlsafe(24)
 bob.ok('/auth/reset','POST',{'token':code_from_mail('bob@example.test','reset'),'password':bob_password});bob.login('bob@example.test',bob_password)
 bob.ok('/me/profile','PUT',{'display_name':'Bob'});assert bob.ok('/me')['profile']=='Bob'
 assert len(bob.ok('/me/sessions'))==1;assert any(r['user']['email']=='bob@example.test' and r['mail_status']=='sent' for r in admin.ok('/admin/users'));passed('Administrator invitation, mail status, user profile and sessions')
 bob.ok('/me/password','PUT',{'current_password':bob_password,'password':password});assert bob.call('/me')[0]==401;bob.login('bob@example.test',password);passed('Authenticated password change invalidates sessions')
 bob_device=bob.ok('/portal/clients','POST',{'name':'delete-test'});bob.ok('/portal/tunnels','POST',{'name':'delete-test','client_id':bob_device['id'],'protocol':'tcp','local_host':'127.0.0.1','local_port':19201,'enabled':True,'bandwidth_limit_bps':100000})
 bobid=bob.ok('/me')['user']['id'];admin.ok('/admin/users/'+bobid,'PUT',{'status':'deleted','role':'user'});assert bob.call('/me')[0]==401;assert all(r['user']['email']!='bob@example.test' for r in admin.ok('/admin/users'));passed('User deletion revokes resources and clears personal data')
 result={'rate_report':rate_report,'passed':len(checks),'checks':checks,'tcp_shared_seconds':round(elapsed,3),'run':str(run)};(out/'latest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:
 for proc in reversed(processes):
  if proc.poll() is None:
   proc.terminate()
   try:proc.wait(timeout=8)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
 for s in servers:s.shutdown();s.server_close()
 for h in handles:h.close()
