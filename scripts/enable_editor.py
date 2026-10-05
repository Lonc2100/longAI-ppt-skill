"""Create a new standalone editable HTML version without overwriting the source.
Requires beautifulsoup4. All runtime assets are embedded; no network at runtime.
"""
import argparse, base64, hashlib, json, mimetypes, re, shutil, uuid
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment

ROOT=Path(__file__).resolve().parents[1]
def json_script(soup,identifier,value):
    tag=soup.new_tag('script',id=identifier,type='application/json')
    tag.string=json.dumps(value,ensure_ascii=False).replace('<','\\u003c')
    soup.body.append(tag)

def enable(source,output):
    source=Path(source).resolve();output=Path(output).resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty output directory; existing work is never overwritten.')
    original=(source/'index.html').read_text(encoding='utf-8')
    soup=BeautifulSoup(original,'html.parser')
    if soup.find(id='deck-edit-config'):raise ValueError('Already editable. Continue from its embedded deck-edit-state; do not regenerate from old source.')
    def local(ref):
        if re.match(r'^[a-zA-Z]+:|^/',ref):raise ValueError('Expected a local relative resource: '+ref)
        file=(source/ref.split('?')[0]).resolve()
        if not file.is_relative_to(source):raise ValueError('Resource escapes deck directory')
        return file
    def data_url(file):return 'data:'+ (mimetypes.guess_type(file.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(file.read_bytes()).decode()
    for link in list(soup.select('link[rel=stylesheet]')):
        file=local(link['href']);css=file.read_text(encoding='utf-8')
        def css_ref(m):
            ref=m.group(1).strip(' \"\'')
            if ref.startswith('data:'):return m.group(0)
            target=(file.parent/ref).resolve()
            if not target.is_relative_to(source):raise ValueError('CSS resource escapes directory')
            return 'url("'+data_url(target)+'")'
        css=re.sub(r'url\(([^)]+)\)',css_ref,css)
        tag=soup.new_tag('style');tag.string=css;link.replace_with(tag)
    for script in soup.select('script[src]'):
        content=(ROOT/'templates/player.js' if script['src']=='player.js' else local(script['src'])).read_text(encoding='utf-8');del script['src'];script.string=content.replace('</script','<\\/script')
    for image in soup.select('img[src]'):
        if not image['src'].startswith('data:'):image['src']=data_url(local(image['src']))
    config={'schema':1,'deckId':str(uuid.uuid4()),'baseVersion':hashlib.sha256(original.encode()).hexdigest()[:16],'text':{},'media':[]}
    for i,slide in enumerate(soup.select('.slide'),1):
        slide['data-slide-id']=f'slide-{i}'
        count=0
        for node in list(slide.descendants):
            if not isinstance(node,NavigableString) or isinstance(node,Comment) or not str(node).strip():continue
            if any(p.name in ('script','style','svg','noscript') or 'speaker-notes' in p.get('class',[]) or p.get('aria-hidden')=='true' for p in node.parents):continue
            count+=1;identifier=f'slide-{i}.text-{count}'
            wrapper=soup.new_tag('dd-text');wrapper['data-edit-id']=identifier;wrapper.string=str(node);node.replace_with(wrapper);config['text'][identifier]=str(node)
        for j,img in enumerate(slide.select('img'),1):
            identifier=f'slide-{i}.image-{j}';img['data-edit-media']=identifier;config['media'].append(identifier)
    json_script(soup,'deck-edit-config',config)
    json_script(soup,'deck-edit-state',{'schema':1,'deckId':config['deckId'],'baseVersion':config['baseVersion'],'revision':0,'text':{},'media':{}})
    css=soup.new_tag('style',id='design-deck-editor-css');css.string=(ROOT/'templates/editor.css').read_text(encoding='utf-8');soup.head.append(css)
    licenses='PptxGenJS 4.0.1\n'+(ROOT/'templates/vendor/pptxgenjs-LICENSE.txt').read_text(encoding='utf-8')+'\nJSZip 3.10.1 (MIT option selected)\n'+(ROOT/'templates/vendor/jszip-LICENSE.markdown').read_text(encoding='utf-8')+'\nhtml2canvas 1.4.1\n'+(ROOT/'templates/vendor/html2canvas-LICENSE.txt').read_text(encoding='utf-8')
    json_script(soup,'third-party-licenses',{'licenses':licenses})
    for name in ['vendor/pptxgen.bundle.js','vendor/html2canvas.min.js','pptx-export.js','editor.js']:
        tag=soup.new_tag('script');tag['data-design-deck-module']=name;tag.string=(ROOT/'templates'/name).read_text(encoding='utf-8').replace('</script','<\\/script');soup.body.append(tag)
    output.mkdir(parents=True,exist_ok=True)
    (output/'index.html').write_text(str(soup),encoding='utf-8')
    (output/'THIRD-PARTY-NOTICES.txt').write_text(licenses,encoding='utf-8')
    for name in ['DESIGN.md','outline.md','sources.md']:
        if (source/name).is_file():shutil.copy2(source/name,output/name)
    shutil.copy2(ROOT/'scripts/serve_editor.py',output/'serve_editor.py')
    (output/'打开本地编辑器.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\npython serve_editor.py --open\r\n',encoding='ascii')
    (output/'README.md').write_text('''# 可编辑演示稿

直接双击 index.html，点击底部“编辑 / 导出”。文字可直接输入；点击照片可换图、调左右/上下位置及放大。支持撤销、重做，编辑时暂停动画，退出后恢复放映。

浏览器草稿只属于当前浏览器。点击“保存到 HTML 文件”选择文件保存（支持的浏览器），或“下载可编辑 HTML”带走单文件。照片、样式、播放器及导出库均已内嵌，换电脑不需要旁边的素材文件夹。导出时请完成中文输入。

若希望自动保存回项目：安装Python 3.10+后双击“打开本地编辑器.cmd”。只监听127.0.0.1；修改后回写本目录index.html，并保留首次打开时的备份。多窗口冲突会阻止覆盖。关闭终端即停止服务。

导出PowerPoint：按钮生成真正的.pptx；文字为原生可编辑文本框，照片/渐变/装饰合成背景。HTML动画不转换，原生图表/逐对象照片编辑不在本版范围。字体缺失可能改变PPTX显示。修改后应重新导出。

交给AI接着改：提供最新保存的HTML或“下载修改记录”。嵌入的deck-edit-state是用户最新修改，优先于旧outline.md；不可运行旧构建脚本覆盖。HTML中的固定ID不可按当前顺序重新编号。

第三方库为PptxGenJS与html2canvas，许可见THIRD-PARTY-NOTICES.txt。未使用Dashi的AGPL代码或专有导出引擎。
''',encoding='utf-8')
    return {'output':str(output),'editable_text':len(config['text']),'editable_images':len(config['media']),'deckId':config['deckId']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    print(json.dumps(enable(a.source,a.output),ensure_ascii=False,indent=2))
