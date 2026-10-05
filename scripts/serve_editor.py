"""Optional localhost editor: revision-checked atomic save of known editable fields only."""
import argparse, hashlib, json, os, re, secrets, threading, webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PATTERN=r'(<script\b[^>]*\bid=[\"\']%s[\"\'][^>]*>)([\s\S]*?)(</script>)'
def block(html,name):
    match=re.search(PATTERN%re.escape(name),html)
    if not match:raise ValueError('Missing '+name)
    return json.loads(match[2])
def valid(state,config):
    if not isinstance(state,dict) or set(state)-{'schema','deckId','baseVersion','revision','text','media','updatedAt'}:return False
    if state.get('schema')!=1 or state.get('deckId')!=config['deckId'] or state.get('baseVersion')!=config['baseVersion']:return False
    if type(state.get('revision')) is not int or not 0<=state['revision']<2**53:return False
    if not isinstance(state.get('text'),dict) or not isinstance(state.get('media'),dict):return False
    if any(k not in config['text'] or not isinstance(v,str) or len(v)>20000 for k,v in state['text'].items()):return False
    for k,v in state['media'].items():
        if k not in config['media'] or not isinstance(v,dict) or set(v)!={'src','x','y','zoom'}:return False
        if not isinstance(v['src'],str) or len(v['src'])>16000000 or not re.fullmatch(r'data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+',v['src']):return False
        if any(type(v[x]) not in (int,float) for x in ('x','y','zoom')):return False
        if not(0<=v['x']<=100 and 0<=v['y']<=100 and 1<=v['zoom']<=2):return False
    return True

def serve(root,port=0,open_browser=False):
    root=Path(root).resolve();file=root/'index.html';config=block(file.read_text(encoding='utf-8'),'deck-edit-config')
    token=secrets.token_urlsafe(24);lock=threading.Lock();backup_done=False
    def etag():return hashlib.sha256(file.read_bytes()).hexdigest()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
        def log_message(self,*a):pass
        def reply(self,code,data):
            raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json;charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
        def allowed_host(self):return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
        def do_GET(self):
            if not self.allowed_host():return self.reply(403,{'error':'Host not allowed'})
            if self.path=='/api/info':return self.reply(200,{'token':token,'etag':etag(),'deckId':config['deckId']})
            if self.path.split('?')[0] not in ('/','/index.html','/favicon.ico'):return self.reply(404,{'error':'Not found'})
            super().do_GET()
        def do_POST(self):
            nonlocal backup_done
            origin=f'http://127.0.0.1:{self.server.server_port}'
            if not self.allowed_host() or self.headers.get('Origin')!=origin or self.headers.get('X-Deck-Token')!=token:return self.reply(403,{'error':'Same-origin session required'})
            if self.path!='/api/save':return self.reply(404,{'error':'Not found'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<48*1024*1024:return self.reply(413,{'error':'State too large'})
                state=json.loads(self.rfile.read(length))
            except (ValueError,UnicodeError):return self.reply(400,{'error':'Invalid JSON'})
            if not valid(state,config):return self.reply(400,{'error':'Invalid editable fields'})
            with lock:
                if self.headers.get('If-Match')!=etag():return self.reply(409,{'error':'File changed; reload before saving'})
                original=file.read_text(encoding='utf-8');current=block(original,'deck-edit-state')
                if state['revision']<current['revision']:return self.reply(409,{'error':'Old revision'})
                raw=json.dumps(state,ensure_ascii=False).replace('<','\\u003c')
                updated=re.sub(PATTERN%'deck-edit-state',lambda m:m[1]+raw+m[3],original,count=1)
                if not backup_done:
                    backup=root/('index.before-edit-'+secrets.token_hex(4)+'.html');backup.write_text(original,encoding='utf-8');backup_done=True
                temp=root/('.index-'+secrets.token_hex(8)+'.tmp');temp.write_text(updated,encoding='utf-8');os.replace(temp,file)
                self.reply(200,{'etag':etag(),'revision':state['revision']})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);url=f'http://127.0.0.1:{server.server_port}/'
    (root/'editor-session.json').write_text(json.dumps({'url':url,'pid':os.getpid()}),encoding='utf-8')
    print(url,flush=True)
    if open_browser:webbrowser.open(url)
    server.serve_forever()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).parent);p.add_argument('--port',type=int,default=0);p.add_argument('--open',action='store_true');a=p.parse_args();serve(a.root,a.port,a.open)
