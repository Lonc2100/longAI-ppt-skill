"""Focused regressions for non-destructive init, moved folders, and source updates."""
import argparse
import copy
import json
from pathlib import Path
from init_deck import create, ROOT
from check_deck import check
from build_examples import slides, DATA

def run(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);checks=[]
    def record(name,ok):checks.append({'name':name,'ok':bool(ok)})
    first=create(output/'中文 带空格','playful','新标题 <不是标签> & 中文')
    text=(first/'index.html').read_text(encoding='utf-8')
    record('title-html-escaped','&lt;不是标签&gt; &amp; 中文' in text and '<不是标签>' not in text)
    before={p.name:p.read_bytes() for p in first.iterdir() if p.is_file()}
    try:create(first,'playful','不能覆盖');record('nonempty-rejected',False)
    except FileExistsError:record('nonempty-rejected',True)
    record('original-preserved',before=={p.name:p.read_bytes() for p in first.iterdir() if p.is_file()})
    try:create(output/'unknown','unknown','标题');record('unknown-rejected',False)
    except ValueError:record('unknown-rejected',True)
    record('unknown-no-output',not (output/'unknown').exists())
    record('starter-not-passed-as-finished',not check(first)['ok'])
    data=copy.deepcopy(DATA);data['sessions'][-1]['speakers']=16
    changed=slides('project-journal',data)
    record('data-ratio-recalculated','66.7%' in changed and '75.0%' not in changed)
    record('data-chart-recalculated','--value:66.666667%' in changed and '16 / 24 人' in changed)
    record('notes-recalculated','8、12、15、16 人' in changed and '8、12、15、18 人' not in changed)
    for style in ('playful','commerce-intelligence','project-journal'):
        s=slides(style,DATA);record('six-pages-'+style,s.count('<section class="slide ')==6)
    record('process-total',sum(x['minutes'] for x in DATA['process'])==25)
    record('no-runtime-network',all('https://' not in (ROOT/'examples'/n/'index.html').read_text(encoding='utf-8') for n in ('playful','commerce-intelligence','reading-circle')))
    r={'ok':all(c['ok'] for c in checks),'checks':checks,'scope':'deterministic mechanics and synthetic source update; not model behavior'}
    (output/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return r

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path,help='New evidence directory, preserved after test');a=p.parse_args();r=run(a.output);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['ok'] else 2)
if __name__=='__main__':main()
