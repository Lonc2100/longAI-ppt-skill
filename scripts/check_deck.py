"""Static deck contract check; this does not verify visual quality."""
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.slides=[]; self.resources=[]; self.errors=[]; self.ids=set(); self.editable=[]; self.media=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'data-edit-id' in a:self.editable.append(a['data-edit-id'])
        if 'data-edit-media' in a:self.media.append(a['data-edit-media'])
        if 'id' in a:
            if a['id'] in self.ids: self.errors.append('Duplicate id: '+a['id'])
            self.ids.add(a['id'])
        if 'slide' in a.get('class','').split():
            self.slides.append(a.get('data-title',''))
            if not a.get('data-title'): self.errors.append('Slide missing data-title')
        for key in ('src','href'):
            if key in a and not a[key].startswith('#'): self.resources.append(a[key])
        for key in ('data-step','data-until'):
            if key in a and not re.fullmatch(r'\d+',a[key]): self.errors.append('Invalid '+key)
        if 'data-step' in a and 'data-until' in a and a['data-step'].isdigit() and a['data-until'].isdigit() and int(a['data-until'])<int(a['data-step']): self.errors.append('data-until precedes data-step')

def check(root):
    root=Path(root).resolve(); errors=[]
    html=(root/'index.html').read_text(encoding='utf-8') if (root/'index.html').is_file() else ''
    parser=DeckParser();parser.feed(html)
    standalone='deck-edit-config' in parser.ids
    required=['index.html','DESIGN.md','outline.md','sources.md','README.md']
    if not standalone:required+=['base.css','theme.css','custom.css','player.js']
    else:required+=['THIRD-PARTY-NOTICES.txt']
    for name in required:
        if not (root/name).is_file(): errors.append('Missing: '+name)
    if errors: return {'ok':False,'errors':errors,'kind':'static'}
    errors.extend(parser.errors)
    if standalone:
        if len(set(parser.editable))!=len(parser.editable) or len(set(parser.media))!=len(parser.media):errors.append('Duplicate editable ID')
        try:
            from serve_editor import block,valid
            config=block(html,'deck-edit-config');state=block(html,'deck-edit-state')
            if set(config['text'])!=set(parser.editable) or set(config['media'])!=set(parser.media):errors.append('Editable IDs disagree with config')
            if not valid(state,config):errors.append('Invalid embedded edit state')
        except (ValueError,KeyError,TypeError):errors.append('Malformed embedded edit config/state')
        for module in ('editor.js','pptx-export.js','vendor/pptxgen.bundle.js','vendor/html2canvas.min.js'):
            if f'data-design-deck-module="{module}"' not in html:errors.append('Missing embedded module: '+module)
    if not parser.slides: errors.append('No slides')
    for ref in parser.resources:
        url=urlsplit(ref)
        if url.scheme=='data': continue
        if url.scheme or url.netloc: errors.append('External/absolute runtime reference: '+ref); continue
        target=(root/unquote(url.path)).resolve()
        if not target.is_relative_to(root): errors.append('Resource escapes output folder: '+ref)
        elif not target.is_file(): errors.append('Missing local resource: '+ref)
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix not in ('.css','.js','.html','.md','.json') or 'qa' in path.relative_to(root).parts: continue
        text=path.read_text(encoding='utf-8')
        # Upstream bundled code contains examples/comments, not authoring placeholders.
        # Its pinned hashes and licenses are checked separately; inspect deck code normally.
        if path.suffix=='.html':text=re.sub(r'<script\b[^>]*data-design-deck-module="vendor/[^\"]+"[^>]*>[\s\S]*?</script>','',text)
        if re.search(r'待填：|\bTODO\b|lorem ipsum|\{\{(?:TITLE|STYLE)\}\}',text,re.I): errors.append('Unfinished placeholder: '+path.name)
        if re.search(r'(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file:///|/Users/|/home/)',text): errors.append('Machine-specific path: '+path.name)
        if path.suffix=='.css':
            for raw in re.findall(r'url\([\s\"\']*([^\)\"\']+)',text):
                if raw.startswith('data:'): continue
                target=(path.parent/unquote(raw)).resolve()
                if urlsplit(raw).scheme or raw.startswith('//') or not target.is_relative_to(root) or not target.is_file(): errors.append('Invalid CSS resource: '+raw)
    return {'ok':not errors,'kind':'static','slides':len(parser.slides),'titles':parser.slides,'errors':errors,'limitations':['No visual inspection','No semantic/source verification']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('deck',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();result=check(a.deck)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['ok'] else 2)
if __name__=='__main__':main()
