"""Portable package validation: links, one entrypoint, themes, source syntax."""
import argparse
import ast
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from check_deck import DeckParser, check

def validate(root):
    root=Path(root).resolve();errors=[]
    required=['SKILL.md','README.md','manifest.json','agents/interface.yaml','LICENSE','gallery/index.html','designs/catalog.json','reports/skill-ir.json','reports/trigger-eval.json','reports/prior-art-research.md','reports/creation-handoff.md']
    for rel in required:
        if not (root/rel).is_file():errors.append('Missing '+rel)
    if [p.relative_to(root).as_posix() for p in root.rglob('SKILL.md')]!=['SKILL.md']:errors.append('Exactly one root SKILL.md required')
    if not (root/'SKILL.md').is_file():return {'ok':False,'errors':errors}
    skill=(root/'SKILL.md').read_text(encoding='utf-8')
    if not skill.startswith('---\n') or 'name: design-deck' not in skill or 'description:' not in skill:errors.append('Invalid frontmatter')
    for path in root.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:continue
        rel=path.relative_to(root).as_posix()
        if path.suffix=='.py':
            try:ast.parse(path.read_text(encoding='utf-8'))
            except SyntaxError as exc:errors.append(f'{rel}: {exc}')
        if path.suffix=='.json':
            try:json.loads(path.read_text(encoding='utf-8'))
            except ValueError:errors.append('Invalid JSON '+rel)
        if path.suffix not in ('.md','.html'):continue
        text=path.read_text(encoding='utf-8');links=re.findall(r'\]\(([^)]+)\)',text) if path.suffix=='.md' else []
        if path.suffix=='.html' and 'templates' not in path.relative_to(root).parts:
            parser=DeckParser();parser.feed(text);links.extend(parser.resources)
        for ref in links:
            url=urlsplit(ref)
            if url.scheme or url.netloc or not url.path:continue
            target=(path.parent/unquote(url.path)).resolve()
            if not target.is_relative_to(root) or not target.exists():errors.append(f'Broken/outside link in {rel}: {ref}')
    catalog=json.loads((root/'designs/catalog.json').read_text(encoding='utf-8'))
    if len({c['id'] for c in catalog})!=len(catalog):errors.append('Duplicate style id')
    decks=[]
    for c in catalog:
        for key in ('design','css','example'):
            target=(root/c[key]).resolve()
            if not target.is_relative_to(root) or not target.is_file():errors.append('Missing/outside catalog resource: '+c[key])
        result=check((root/c['example']).parent);decks.append({'style':c['id'],**result})
        errors.extend(f"{c['id']}: {e}" for e in result['errors'])
    return {'ok':not errors,'errors':errors,'themes':len(catalog),'decks':decks,'scope':'static package checks only'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path);a=p.parse_args();r=validate(a.root)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['ok'] else 2)
if __name__=='__main__':main()
