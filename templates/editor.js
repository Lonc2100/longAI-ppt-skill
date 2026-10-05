/* Original Design Deck editing implementation. No Dashi source incorporated. */
(() => {
  'use strict';
  const configEl=document.getElementById('deck-edit-config');
  if(!configEl || !window.deck) return;
  const config=JSON.parse(configEl.textContent), stateEl=document.getElementById('deck-edit-state');
  const baseline='<!doctype html>\n'+document.documentElement.outerHTML;
  const copy=v=>JSON.parse(JSON.stringify(v)), $=id=>document.getElementById(id);
  const textNodes=new Map([...document.querySelectorAll('[data-edit-id]')].map(n=>[n.dataset.editId,n]));
  const images=new Map([...document.querySelectorAll('[data-edit-media]')].map(n=>[n.dataset.editMedia,n]));
  const imageBase=new Map([...images].map(([id,n])=>[id,{src:n.getAttribute('src'),position:n.style.objectPosition,transform:n.style.transform}]));
  const fresh=()=>({schema:1,deckId:config.deckId,baseVersion:config.baseVersion,revision:0,text:{},media:{}});
  let embedded=JSON.parse(stateEl.textContent), state=valid(embedded)?embedded:fresh();
  let edit=false,selected=null,changed=false,fileHandle=null,composing=false,focusBefore=null,busy=false;
  let history=[],future=[],diskETag=null,serverToken=null,saveTimer=null,saving=false,resave=false,conflict=false;
  const key=`design-deck:${config.deckId}:${config.baseVersion}`;
  let recovered=false,draftOK=true;
  try {const d=JSON.parse(localStorage.getItem(key)||'null');if(valid(d)&&d.revision>state.revision){state=d;recovered=true;changed=true;}}catch{}
  function valid(s){
    return !!s && s.schema===1 && s.deckId===config.deckId && s.baseVersion===config.baseVersion && Number.isSafeInteger(s.revision) && s.revision>=0
      && s.text && typeof s.text==='object' && !Array.isArray(s.text) && s.media && typeof s.media==='object' && !Array.isArray(s.media)
      && Object.entries(s.text).every(([id,v])=>textNodes.has(id)&&typeof v==='string'&&v.length<=20000)
      && Object.entries(s.media).every(([id,v])=>images.has(id)&&v&&typeof v==='object'&&typeof v.src==='string'&&/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(v.src)&&v.src.length<16000000&&['x','y','zoom'].every(k=>Number.isFinite(v[k]))&&v.x>=0&&v.x<=100&&v.y>=0&&v.y<=100&&v.zoom>=1&&v.zoom<=2);
  }
  const toggle=document.createElement('button');toggle.id='dd-toggle';toggle.textContent='编辑 / 导出';toggle.setAttribute('aria-expanded','false');document.querySelector('.toolbar').append(toggle);
  const panel=document.createElement('aside');panel.id='dd-panel';panel.hidden=true;panel.setAttribute('aria-label','演示编辑工具');
  panel.innerHTML=`<h2>编辑这份演示</h2><p>点击文字直接输入，点击照片换图。</p><div id="dd-status" role="status" aria-live="polite"></div><div class="dd-row"><button id="dd-undo" title="Ctrl+Z">撤销</button><button id="dd-redo" title="Ctrl+Shift+Z">重做</button><button id="dd-done">完成编辑</button></div><p id="dd-warning" hidden></p><div id="dd-image-tools" hidden><h3>当前照片</h3><p id="dd-selection"></p><button id="dd-replace">选择新照片</button><input id="dd-file" type="file" accept="image/png,image/jpeg,image/webp" hidden><label>左右位置<input id="dd-x" type="range" min="0" max="100" value="50"></label><label>上下位置<input id="dd-y" type="range" min="0" max="100" value="50"></label><label>放大<input id="dd-zoom" type="range" min="1" max="2" step="0.01" value="1"></label></div><hr><h3>保存与带走</h3><button id="dd-save" class="dd-wide dd-primary">保存到 HTML 文件</button><button id="dd-download" class="dd-wide">下载可编辑 HTML</button><button id="dd-pptx" class="dd-wide">导出 PowerPoint（.pptx）</button><p>HTML 单文件含照片与编辑器，可离线使用。浏览器草稿不是文件备份。</p><p>PPTX：文字可编辑；照片、渐变与装饰合成背景，不保留动画。</p><button id="dd-record" class="dd-wide">下载修改记录（交给 AI）</button>`;
  document.body.append(panel);
  function status(message){$('dd-status').textContent=message;}
  function setStateElement(){stateEl.textContent=JSON.stringify(state).replace(/</g,'\\u003c');}
  function persist(){
    setStateElement();draftOK=true;
    try{localStorage.setItem(key,JSON.stringify(state));}catch{draftOK=false;}
    status(draftOK?'草稿已保存在本浏览器；文件尚未保存':'浏览器草稿空间不足，请立即保存 HTML 文件');
    if(serverToken&&!conflict){clearTimeout(saveTimer);saveTimer=setTimeout(saveServer,650);}
  }
  function apply(){
    for(const [id,n] of textNodes)n.textContent=Object.hasOwn(state.text,id)?state.text[id]:config.text[id];
    for(const [id,n] of images){const m=state.media[id],b=imageBase.get(id);n.src=m?.src||b.src;n.style.objectPosition=m?`${m.x}% ${m.y}%`:b.position;n.style.transform=m?`scale(${m.zoom})`:b.transform;}
    document.querySelectorAll('.slide').forEach((slide,i)=>{const h=slide.querySelector('h1,h2');if(!h)return;const title=h.textContent.replace(/\s+/g,' ').trim();slide.dataset.title=title;const b=document.querySelector(`[data-jump="${i}"]`);if(b)b.textContent=`${String(i+1).padStart(2,'0')}  ${title}`;});
    setStateElement();buttons();
  }
  function buttons(){$('dd-undo').disabled=!history.length;$('dd-redo').disabled=!future.length;}
  function commit(before){
    if(JSON.stringify(before.text)===JSON.stringify(state.text)&&JSON.stringify(before.media)===JSON.stringify(state.media))return;
    history.push(before);if(history.length>80)history.shift();future=[];state.revision++;state.updatedAt=new Date().toISOString();changed=true;persist();buttons();checkLayout();
  }
  function updateText(n){const v=n.innerText.replace(/\r/g,'');if(v===config.text[n.dataset.editId])delete state.text[n.dataset.editId];else state.text[n.dataset.editId]=v;setStateElement();}
  function flush(){if(composing)throw new Error('请先完成当前中文输入，再保存或导出。');if(document.activeElement?.matches('[data-edit-id]'))document.activeElement.blur();}
  function undo(){flush();if(!history.length)return;const revision=state.revision+1;future.push(copy(state));state=history.pop();state.revision=revision;changed=true;apply();persist();checkLayout();}
  function redo(){flush();if(!future.length)return;const revision=state.revision+1;history.push(copy(state));state=future.pop();state.revision=revision;changed=true;apply();persist();checkLayout();}
  function mode(on){
    if(busy)return;flush();edit=on;window.deck.setAuto(false);document.body.classList.toggle('dd-edit',edit);panel.hidden=!edit;toggle.textContent=edit?'退出编辑':'编辑 / 导出';toggle.setAttribute('aria-expanded',String(edit));
    for(const n of textNodes.values()){if(edit){n.setAttribute('contenteditable','plaintext-only');n.setAttribute('role','textbox');n.setAttribute('spellcheck','false');}else{n.removeAttribute('contenteditable');n.removeAttribute('role');n.removeAttribute('spellcheck');}}
    if(!edit){for(const n of images.values())n.classList.remove('dd-selected-image');selected=null;$('dd-image-tools').hidden=true;}
    window.deck.go(window.deck.state.page,window.deck.state.beat,{animate:false});dispatchEvent(new Event('resize'));checkLayout();
  }
  function checkLayout(){
    if(!edit)return;const slide=document.querySelector('.slide.active');if(!slide)return;const sr=slide.getBoundingClientRect();const warnings=[];
    for(const n of slide.querySelectorAll('[data-edit-id]')){const r=n.getBoundingClientRect(),parent=n.parentElement,pr=parent.getBoundingClientRect();const id=n.dataset.editId;
      if(r.left<sr.left-1||r.right>sr.right+1||r.top<sr.top-1||r.bottom>sr.bottom+1||r.right>pr.right+3||parent.scrollHeight>parent.clientHeight+5&&['hidden','clip'].includes(getComputedStyle(parent).overflowY))warnings.push(n.textContent.slice(0,15));
      else if(Object.hasOwn(state.text,id)&&n.textContent.length>config.text[id].length*1.35+4)warnings.push(n.textContent.slice(0,15));
    }
    $('dd-warning').hidden=!warnings.length;$('dd-warning').textContent='文字变长或可能超出区域，请检查排版：\n'+warnings.slice(0,3).join('\n');
  }
  for(const n of textNodes.values()){
    n.addEventListener('focus',()=>{focusBefore=copy(state);});
    n.addEventListener('compositionstart',()=>composing=true);
    n.addEventListener('compositionend',()=>{composing=false;updateText(n);changed=true;checkLayout();});
    n.addEventListener('input',()=>{if(!edit||composing)return;updateText(n);changed=true;status('正在编辑；离开文字框后保存草稿');checkLayout();});
    n.addEventListener('blur',()=>{if(!focusBefore)return;updateText(n);const before=focusBefore;focusBefore=null;commit(before);apply();});
    n.addEventListener('paste',e=>{e.preventDefault();const text=e.clipboardData.getData('text/plain');document.execCommand('insertText',false,text);});
    n.addEventListener('keydown',e=>{if(e.key==='Escape'&&!composing){e.preventDefault();n.blur();}});
  }
  for(const [id,n] of images){n.addEventListener('click',()=>{if(!edit)return;selectImage(id);});n.addEventListener('dragover',e=>{if(edit)e.preventDefault();});n.addEventListener('drop',e=>{if(!edit)return;e.preventDefault();selectImage(id);replaceImage(e.dataTransfer.files[0]).catch(fail);});}
  // Decorative gradient/SVG layers can sit over a photo. Hit-test its visible area.
  function imageAt(e){return [...images].reverse().find(([,n])=>{if(n.closest('.slide')?.hidden)return false;const r=n.getBoundingClientRect();return e.clientX>=r.left&&e.clientX<=r.right&&e.clientY>=r.top&&e.clientY<=r.bottom;})?.[0];}
  $('stage').addEventListener('click',e=>{if(!edit||e.target.closest('[data-edit-id]'))return;const id=imageAt(e);if(id)selectImage(id);});
  $('stage').addEventListener('dragover',e=>{if(edit&&imageAt(e))e.preventDefault();});
  $('stage').addEventListener('drop',e=>{if(!edit||e.target.matches('[data-edit-media]'))return;const id=imageAt(e);if(id){e.preventDefault();selectImage(id);replaceImage(e.dataTransfer.files[0]).catch(fail);}});
  function selectImage(id){selected=id;for(const [key,n] of images)n.classList.toggle('dd-selected-image',key===id);$('dd-image-tools').hidden=false;$('dd-selection').textContent=images.get(id).alt||'所选照片';const m=state.media[id]||imageValue(id);$('dd-x').value=m.x;$('dd-y').value=m.y;$('dd-zoom').value=m.zoom;}
  function imageValue(id){const n=images.get(id),pos=getComputedStyle(n).objectPosition.split(' ').map(parseFloat);return{src:n.src,x:Number.isFinite(pos[0])?pos[0]:50,y:Number.isFinite(pos[1])?pos[1]:50,zoom:1};}
  async function replaceImage(file){
    if(!file||!selected)return;if(!/^image\/(png|jpeg|webp)$/.test(file.type))throw new Error('请选择 PNG、JPEG 或 WebP 照片。');if(file.size>30*1024*1024)throw new Error('照片超过30MB，请先缩小后再选择。');
    const id=selected;const bitmap=await createImageBitmap(file);const c=document.createElement('canvas');const ratio=Math.min(1,2400/Math.max(bitmap.width,bitmap.height));c.width=Math.round(bitmap.width*ratio);c.height=Math.round(bitmap.height*ratio);c.getContext('2d').drawImage(bitmap,0,0,c.width,c.height);bitmap.close();
    const before=copy(state);state.media[id]={src:c.toDataURL('image/webp',.92),x:50,y:50,zoom:1};apply();commit(before);selectImage(id);
  }
  let cropBefore=null;
  for(const [control,prop] of [['dd-x','x'],['dd-y','y'],['dd-zoom','zoom']]){
    $(control).addEventListener('input',()=>{if(!selected)return;if(!cropBefore)cropBefore=copy(state);state.media[selected]??=imageValue(selected);state.media[selected][prop]=Number($(control).value);apply();});
    $(control).addEventListener('change',()=>{if(cropBefore){commit(cropBefore);cropBefore=null;}});
  }
  function htmlForState(s){const doc=new DOMParser().parseFromString(baseline,'text/html');doc.getElementById('page-list').replaceChildren();doc.getElementById('deck-edit-state').textContent=JSON.stringify(s).replace(/</g,'\\u003c');return '<!doctype html>\n'+doc.documentElement.outerHTML;}
  function download(blob,name){const a=document.createElement('a'),u=URL.createObjectURL(blob);a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),30000);}
  function downloadHtml(){flush();download(new Blob([htmlForState(state)],{type:'text/html;charset=utf-8'}),document.title.replace(/[\\/:*?"<>|]/g,'_')+'_可编辑.html');status('已发起 HTML 下载；请确认下载完成后保留文件');changed=false;}
  async function saveFile(){
    flush();if(serverToken&&!conflict){await saveServer();return;}
    if(!window.showSaveFilePicker){downloadHtml();return;}
    try{fileHandle??=await showSaveFilePicker({suggestedName:'演示稿_可编辑.html',types:[{description:'可编辑 HTML',accept:{'text/html':['.html']}}]});const snap=copy(state);const stream=await fileHandle.createWritable();await stream.write(htmlForState(snap));await stream.close();if(state.revision===snap.revision){changed=false;status('已保存到所选 HTML 文件');}else status('上一版已保存；仍有新修改，请再次保存');}
    catch(e){if(e.name!=='AbortError')throw e;}
  }
  async function saveServer(){
    flush();if(!serverToken||conflict)return;if(saving){resave=true;return;}saving=true;const snap=copy(state);status('正在保存到项目文件…');
    try{const r=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json','X-Deck-Token':serverToken,'If-Match':diskETag},body:JSON.stringify(snap)});if(r.status===409){conflict=true;throw new Error('文件已被其他窗口修改。请先下载当前 HTML 备份，再刷新合并，未覆盖文件。');}if(!r.ok)throw new Error('项目保存失败；请下载 HTML 备份。');const data=await r.json();diskETag=data.etag;if(state.revision===snap.revision){changed=false;status('已保存到项目文件 index.html');}else{resave=true;status('正在保存后续修改…');}}
    catch(e){status(e.message);}finally{saving=false;if(resave&&!conflict){resave=false;setTimeout(saveServer,100);}}
  }
  async function connect(){if(!['http:','https:'].includes(location.protocol))return;try{const r=await fetch('/api/info');if(!r.ok)return;const d=await r.json();if(d.deckId!==config.deckId)return;diskETag=d.etag;serverToken=d.token;if(recovered)saveServer();else status('本地编辑服务已连接；修改后自动保存到文件');}catch{}}
  function fail(e){status(e.message||String(e));}
  toggle.onclick=()=>mode(!edit);$('dd-done').onclick=()=>mode(false);$('dd-undo').onclick=undo;$('dd-redo').onclick=redo;
  $('dd-replace').onclick=()=>$('dd-file').click();$('dd-file').onchange=()=>{replaceImage($('dd-file').files[0]).catch(fail);$('dd-file').value='';};
  $('dd-save').onclick=()=>saveFile().catch(fail);$('dd-download').onclick=()=>{try{downloadHtml();}catch(e){fail(e);}};
  $('dd-record').onclick=()=>{flush();download(new Blob([JSON.stringify({config:{deckId:config.deckId,baseVersion:config.baseVersion},state,content:[...textNodes].map(([id,n])=>({id,text:n.textContent})),note:'用户直接编辑后的最新状态。应先应用到本版本，再由AI继续修改；原outline.md仅为历史确认稿。'},null,2)],{type:'application/json'}),'修改记录.json');};
  $('dd-pptx').onclick=async()=>{try{flush();busy=true;await window.designDeckPptx.export();}catch(e){fail(e);}finally{busy=false;}};
  document.addEventListener('keydown',e=>{
    if(!edit||busy)return;
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();saveFile().catch(fail);return;}
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&!composing){e.preventDefault();e.stopImmediatePropagation();e.shiftKey?redo():undo();return;}
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'&&!composing){e.preventDefault();e.stopImmediatePropagation();redo();return;}
    if(e.target.closest('[contenteditable],#dd-panel')){e.stopImmediatePropagation();return;}
    if(['ArrowRight','ArrowLeft','PageDown','PageUp'].includes(e.key)){e.preventDefault();e.stopImmediatePropagation();window.deck.go(window.deck.state.page+(['ArrowRight','PageDown'].includes(e.key)?1:-1),0);checkLayout();}
    else if([' ','p','P'].includes(e.key)){e.preventDefault();e.stopImmediatePropagation();}
  },true);
  document.addEventListener('pointerdown',e=>{if(edit&&e.pointerType==='touch'&&e.target.closest('#stage'))e.stopPropagation();},true);
  addEventListener('beforeunload',e=>{if(changed){e.preventDefault();e.returnValue='';}});
  apply();status(recovered?'已恢复本浏览器草稿；请保存到文件':'未修改。进入编辑后点击文字或照片。');connect();
  window.designDeckEditor={get state(){return copy(state);},get editing(){return edit;},mode,flush,undo,redo,serialize:()=>{flush();return htmlForState(state);},download,applyState(s){if(!valid(s))throw new Error('修改记录与当前演示不匹配');const before=copy(state);state=copy(s);apply();commit(before);},config};
})();
