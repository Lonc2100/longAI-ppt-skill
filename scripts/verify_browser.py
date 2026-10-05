"""Render a deck offline and exercise playback; requires Playwright/Chromium."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from check_deck import check

GEOMETRY = '''() => {
 const s=document.querySelector('.slide.active'), issues=[];
 for(const e of s.querySelectorAll('*')){
  if(e.closest('svg,.speaker-notes')||e.getAttribute('aria-hidden')==='true'||getComputedStyle(e).visibility==='hidden')continue;
  if(e.children.length||!e.textContent.trim())continue;
  const r=e.getBoundingClientRect(),box=document.querySelector('#stage').getBoundingClientRect();
  if(r.width && r.height && (r.left<box.left-1||r.right>box.right+1||r.top<box.top-1||r.bottom>box.bottom+1))issues.push({type:'stage-overflow',text:e.textContent.slice(0,80)});
  const clipsY=['hidden','clip','auto','scroll'].includes(getComputedStyle(e).overflowY);
  // Font ascenders can extend beyond a tight line box without clipping. Check
  // vertical overflow only for constrained containers; stage bounds stay checked.
  if(e.clientWidth>0&&(e.scrollWidth>e.clientWidth+2||(clipsY&&e.scrollHeight>e.clientHeight+2)))issues.push({type:'text-overflow',text:e.textContent.slice(0,80)});
 }
 return issues;
}'''

def verify(root, browser_path=None):
    try: from playwright.sync_api import sync_playwright
    except ImportError: raise SystemExit('Playwright unavailable; perform manual checks in references/quality.md. No browser pass claimed.')
    root=Path(root).resolve();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=root/'qa'/stamp;out.mkdir(parents=True)
    report={'timestamp_utc':stamp,'static':check(root),'checks':[],'states':0,'errors':[],'geometry':[],'screenshots':[], 'limitations':['Geometry does not detect all overlaps or assess aesthetics','One local Chromium environment only']}
    def record(name, condition):
        report['checks'].append({'name':name,'ok':bool(condition)})
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,**({'executable_path':str(browser_path)} if browser_path else {}))
        report['browser_version']=browser.version
        ctx=browser.new_context(viewport={'width':1600,'height':900},offline=True)
        page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.on('requestfailed',lambda req:report['errors'].append('Resource failed: '+req.url.split('/')[-1]))
        page.goto((root/'index.html').as_uri());page.evaluate('document.fonts.ready');page.wait_for_function('!!window.deck')
        total=page.evaluate('deck.state.total');maxima=page.evaluate("Array.from(document.querySelectorAll('.slide'),s=>Math.max(0,...Array.from(s.querySelectorAll('[data-step]'),e=>Number(e.dataset.step))))")
        expected=[{'page':i,'beat':b} for i,m in enumerate(maxima) for b in range(m+1)]
        record('page-count',total==len(maxima))
        for item in expected:
            page.evaluate('(x)=>deck.go(x.page,x.beat,{animate:false})',item)
            state=page.evaluate('deck.state');record(f"seek-{item['page']}-{item['beat']}",state['page']==item['page'] and state['beat']==item['beat'])
            report['states']+=1
            geometry=page.evaluate(GEOMETRY)
            if geometry:report['geometry'].append({'state':item,'issues':geometry})
            visible=page.evaluate('''()=>Array.from(document.querySelector('.slide.active').querySelectorAll('[data-step]')).every(e=>{
             const expected=deck.state.beat>=Number(e.dataset.step)&&(!e.hasAttribute('data-until')||deck.state.beat<=Number(e.dataset.until));
             return (getComputedStyle(e).visibility!=='hidden')===expected && e.inert===!expected;
            })''');record(f"reveal-{item['page']}-{item['beat']}",visible)
            if item['beat']==maxima[item['page']]:
                name=f"page-{item['page']+1:02d}.png";page.screenshot(path=str(out/name));report['screenshots'].append(name)
        page.evaluate('deck.go(0,0,{animate:false})')
        for item in expected[1:]:
            page.evaluate('deck.next()');s=page.evaluate('deck.state');record('forward',s['page']==item['page'] and s['beat']==item['beat'])
        record('last-boundary',page.locator('#next').is_disabled())
        page.evaluate('deck.next()');s=page.evaluate('deck.state');record('last-clamped',s['page']==total-1 and s['beat']==maxima[-1])
        for item in reversed(expected[:-1]):
            page.evaluate('deck.prev()');s=page.evaluate('deck.state');record('backward',s['page']==item['page'] and s['beat']==item['beat'])
        record('first-boundary',page.locator('#prev').is_disabled());page.evaluate('deck.prev()');record('first-clamped',page.evaluate('deck.state.page===0&&deck.state.beat===0'))
        page.locator('#overview').click();record('menu-open',page.locator('#menu').is_visible());page.locator(f'[data-jump="{total-1}"]').click();record('menu-jump',page.evaluate(f'deck.state.page==={total-1}&&document.querySelector("#menu").hidden'))
        page.locator('#notes').click();record('notes',page.locator('#notes-panel').is_visible() and bool(page.locator('#notes-text').inner_text().strip()));page.keyboard.press('Escape')
        page.evaluate('deck.go(0,0,{animate:false})');page.keyboard.press('ArrowRight');record('keyboard-next',page.evaluate('deck.state.beat')==min(1,maxima[0]));page.keyboard.press('Home');record('keyboard-home',page.evaluate('deck.state.page===0&&deck.state.beat===0'))
        original=page.locator('.slide').first.get_attribute('data-delay')
        page.evaluate("document.querySelector('.slide').dataset.delay='1000';deck.setAuto(true)")
        page.wait_for_timeout(1150);record('autoplay-advances-or-single-state-stops',page.evaluate('deck.state.beat>0||deck.state.page>0') if len(expected)>1 else page.evaluate('!deck.state.auto'))
        page.keyboard.press('Escape');record('escape-pauses',page.evaluate('!deck.state.auto'));state=page.evaluate('deck.state');page.wait_for_timeout(1100);record('paused-stable',state==page.evaluate('deck.state'))
        page.evaluate('(v)=>{const e=document.querySelector(".slide");if(v===null)e.removeAttribute("data-delay");else e.dataset.delay=v;}',original)
        page.evaluate('deck.go(0,0);deck.setAuto(true)');page.locator('#notes').click();record('notes-pauses',page.evaluate('!deck.state.auto'));page.keyboard.press('Escape')
        page.evaluate('(x)=>{deck.go(x[0],x[1]);deck.setAuto(true)}',[total-1,maxima[-1]]);record('end-stops-auto',page.evaluate('!deck.state.auto'))
        page.locator('#full').click();page.wait_for_timeout(100);full=page.evaluate('!!document.fullscreenElement');report['fullscreen_native']=full
        record('fullscreen-or-explicit-fallback',full or page.locator('#player-message').is_visible())
        if full:page.evaluate('document.exitFullscreen()')
        for w,h in [(1024,768),(390,844)]:
            page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(70)
            record(f'fit-{w}x{h}',page.evaluate('''()=>{const r=document.querySelector('#stage').getBoundingClientRect();return r.left>=-1&&r.top>=-1&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1}'''))
            record(f'controls-{w}x{h}',page.locator('#next').is_visible() and page.evaluate("document.querySelector('.toolbar').getBoundingClientRect().width<=innerWidth"))
        page.set_viewport_size({'width':1600,'height':900});page.emulate_media(reduced_motion='reduce');page.evaluate('deck.go(0,0);deck.next()');record('reduced-motion-no-animation',page.evaluate('document.getAnimations().length===0'))
        page.evaluate('location.hash="p=2&b=1"');page.wait_for_timeout(100);target=min(1,total-1);record('hash-seek',page.evaluate(f'deck.state.page==={target}&&deck.state.beat==={min(1,maxima[target])}'))
        ctx.close();browser.close()
    report['ok']=report['static']['ok'] and not report['errors'] and not report['geometry'] and all(x['ok'] for x in report['checks'])
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':report['ok'],'states':report['states'],'checks':len(report['checks']),'errors':report['errors'],'geometry':report['geometry'],'failed':[x for x in report['checks'] if not x['ok']],'report':str(out/'report.json')},ensure_ascii=False))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('deck',type=Path);p.add_argument('--browser',type=Path);a=p.parse_args();raise SystemExit(0 if verify(a.deck,a.browser)['ok'] else 2)
if __name__=='__main__':main()
