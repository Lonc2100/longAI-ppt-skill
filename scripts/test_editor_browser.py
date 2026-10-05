"""Exercise real browser editing, offline roundtrip, PPTX XML and localhost saves.
Uses isolated browser contexts and a separate server fixture; never edits the input deck.
"""
import argparse, hashlib, importlib.util, json, shutil, subprocess, sys, time, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import requests
from playwright.sync_api import sync_playwright

def test(root, chrome):
    root=root.resolve();out=root/'qa'/'editor';out.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[]
    def check(name,ok):
        checks.append({'name':name,'ok':bool(ok)})
        if not ok:raise AssertionError(name)
    initial=hashlib.sha256((root/'index.html').read_bytes()).hexdigest()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=str(chrome),headless=True)
        ctx=browser.new_context(viewport={'width':1600,'height':1000},offline=True,accept_downloads=True)
        page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((root/'index.html').as_uri());page.evaluate('document.fonts.ready')
        check('six slides offline',page.evaluate('deck.state.total')==6)
        page.locator('#dd-toggle').click()
        check('all active beats editable',page.evaluate("[...document.querySelector('.slide.active').querySelectorAll('[data-step]')].every(n=>!n.inert)"))
        target=page.locator('[data-edit-id]').filter(has_text='下班后，').first
        identifier=target.get_attribute('data-edit-id');original=target.inner_text();target=page.locator(f'[data-edit-id="{identifier}"]')
        target.fill('下班以后，');page.keyboard.press('ArrowRight');page.keyboard.press('Space')
        check('typing does not navigate',page.evaluate('deck.state.page')==0)
        target.fill('下班以后，');target.evaluate('(n)=>n.blur()')
        check('Chinese text stored',page.evaluate('designDeckEditor.state.text')[identifier]=='下班以后，')
        page.locator('#dd-undo').click();check('undo text',target.inner_text()==original)
        page.locator('#dd-redo').click();check('redo text',target.inner_text()=='下班以后，')
        target.focus();target.dispatch_event('compositionstart');page.keyboard.press('n')
        check('IME does not open notes',page.locator('#notes-panel').is_hidden())
        target.dispatch_event('compositionend');target.fill('下班以后，');target.evaluate('(n)=>n.blur()')
        with page.expect_download() as d:page.locator('#dd-download').click()
        saved=out/'改字后重新打开.html';d.value.save_as(saved)
        clean=browser.new_context(offline=True,viewport={'width':1600,'height':1000});reopen=clean.new_page();reopen.goto(saved.as_uri())
        check('new browser retains edits',reopen.locator(f'[data-edit-id="{identifier}"]').inner_text()=='下班以后，')
        check('page menu not duplicated',reopen.locator('[data-jump]').count()==6)
        check('license retained',bool(reopen.locator('#third-party-licenses').text_content()))
        clean.close()
        page.reload();page.locator('#dd-toggle').click()
        check('browser draft restored',page.locator(f'[data-edit-id="{identifier}"]').inner_text()=='下班以后，')
        # Click through cover gradient and SVG decorations using actual screen coordinates.
        box=page.locator('.slide.active [data-edit-media]').first.bounding_box()
        page.mouse.click(box['x']+box['width']*.75,box['y']+box['height']*.45)
        check('photo selectable through overlay',page.locator('#dd-image-tools').is_visible())
        source=root.parent/'Skill验证_城市夜行_v002'/'assets'/'bridge.jpg'
        page.locator('#dd-file').set_input_files(str(source));page.wait_for_function('Object.keys(designDeckEditor.state.media).length>0')
        page.locator('#dd-zoom').evaluate("n=>{n.value='1.25';n.dispatchEvent(new Event('input',{bubbles:true}));}");page.locator('#dd-zoom').dispatch_event('change')
        check('photo replacement and crop',page.evaluate('Object.values(designDeckEditor.state.media)[0].zoom')==1.25)
        page.locator('#dd-undo').click();check('undo crop',page.evaluate('Object.values(designDeckEditor.state.media)[0].zoom')==1)
        page.locator('#dd-redo').click();check('redo crop',page.evaluate('Object.values(designDeckEditor.state.media)[0].zoom')==1.25)
        with page.expect_download() as d:page.locator('#dd-download').click()
        photo=out/'换图后重新打开.html';d.value.save_as(photo)
        clean=browser.new_context(offline=True);reopen=clean.new_page();reopen.goto(photo.as_uri())
        check('photo and crop survive file save',reopen.evaluate('Object.values(designDeckEditor.state.media)[0].zoom')==1.25)
        clean.close()
        page.locator('#next').click();check('editor next changes page',page.evaluate('deck.state.page')==1)
        check('revealed text not inert',page.evaluate("[...document.querySelector('.slide.active').querySelectorAll('[data-step]')].every(n=>!n.inert)"))
        page.locator('#dd-done').click();page.evaluate('deck.go(1,0,{animate:false})')
        check('playback beats restored',page.evaluate("[...document.querySelector('.slide.active').querySelectorAll('[data-step]')].filter(n=>Number(n.dataset.step)>0).every(n=>n.inert)"))
        # Use untouched original in a clean context for delivered export and preview.
        ctx.close();ctx=browser.new_context(offline=True,accept_downloads=True,viewport={'width':1600,'height':1000})
        page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((root/'index.html').as_uri());page.locator('#dd-toggle').click()
        page.screenshot(path=str(root/'编辑器预览.png'))
        with page.expect_download(timeout=120000) as d:page.locator('#dd-pptx').click()
        pptx=root/'城市夜行_文字可编辑.pptx';d.value.save_as(pptx)
        check('export restores editor page',page.evaluate('designDeckEditor.editing&&deck.state.page===0'))
        metrics=page.evaluate('designDeckPptx.lastExport');check('six exported pages',metrics['pages']==6)
        with zipfile.ZipFile(pptx) as z:
            check('PPTX zip integrity',z.testzip() is None)
            ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
            text=''
            for i in range(1,7):
                tree=ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
                text+=''.join(n.text or '' for n in tree.findall('.//a:t',ns))
            check('native editable title in PPTX','下班后，把城市还给自己' in text)
            check('native editable data in PPTX','计划招募 24 人' in text)
            check('all measured native text preserved',text==''.join(m['text'] for m in metrics['metrics']))
            (out/'pptx-background-01.png').write_bytes(z.read('ppt/media/image-1-1.png'))
        check('no browser errors',not errors)
        browser.close()
    # Actual server fixture: atomic write, etag conflict and input boundary checks.
    fixture=out/'server-fixture';fixture.mkdir(exist_ok=True)
    shutil.copy2(root/'index.html',fixture/'index.html')
    process=subprocess.Popen([sys.executable,str(root/'serve_editor.py'),'--root',str(fixture)],stdout=subprocess.PIPE,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        url=process.stdout.readline().strip();info=requests.get(url+'api/info',timeout=10).json()
        spec=importlib.util.spec_from_file_location('server',root/'serve_editor.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        state=module.block((fixture/'index.html').read_text(encoding='utf-8'),'deck-edit-state');state['revision']+=1;state['text'][identifier]='本地保存测试'
        headers={'Origin':url.rstrip('/'),'X-Deck-Token':info['token'],'If-Match':info['etag']}
        r=requests.post(url+'api/save',json=state,headers=headers,timeout=10);check('server saves',r.status_code==200)
        check('server file contains exact edit',module.block((fixture/'index.html').read_text(encoding='utf-8'),'deck-edit-state')['text'][identifier]=='本地保存测试')
        check('server backup retained',len(list(fixture.glob('index.before-edit-*.html')))>=1)
        check('stale window rejected',requests.post(url+'api/save',json=state,headers=headers,timeout=10).status_code==409)
        headers['If-Match']=r.json()['etag'];state['text']['not-a-real-id']='bad'
        check('unknown field rejected',requests.post(url+'api/save',json=state,headers=headers,timeout=10).status_code==400)
        check('cross origin rejected',requests.post(url+'api/save',json=state,headers={**headers,'Origin':'https://example.com'},timeout=10).status_code==403)
    finally:process.terminate();process.wait(timeout=10)
    check('delivered original unchanged',hashlib.sha256((root/'index.html').read_bytes()).hexdigest()==initial)
    report={'checks':checks,'errors':errors,'export':metrics,'limitations':['One Windows Chrome environment','IME events simulated; no physical input-method test','PowerPoint/WPS visual rendering not tested; PPTX package and native text checked']}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':len(checks),'report':str(out/'report.json'),'pptx':str(pptx)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('deck',type=Path);p.add_argument('--chrome',type=Path,default=Path('C:/Program Files/Google/Chrome/Application/chrome.exe'));a=p.parse_args();test(a.deck,a.chrome)
