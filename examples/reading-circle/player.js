(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const slides = [...document.querySelectorAll('.slide')];
  if (!slides.length) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const integer = (value, fallback=0) => Number.isFinite(Number(value)) ? Math.trunc(Number(value)) : fallback;
  const maxima = slides.map(s => Math.max(0,...[...s.querySelectorAll('[data-step]')].map(e => integer(e.dataset.step))));
  let page=0, beat=0, playing=false, timer=null, returnFocus=null, animations=[];
  function settle(){ animations.forEach(a=>a.cancel()); animations=[]; }
  function fit(){const v=$('viewport'); $('stage').style.transform=`translate(-50%,-50%) scale(${Math.min(v.clientWidth/1600,v.clientHeight/900)})`;}
  function isEnd(){return page===slides.length-1 && beat===maxima[page];}
  function schedule(){clearTimeout(timer); if(playing && !isEnd()) timer=setTimeout(()=>next(true),Math.max(1000,integer(slides[page].dataset.delay,6000)));}
  function setAuto(on){playing=Boolean(on)&&!isEnd();$('auto').textContent=playing?'暂停':'播放';$('auto').setAttribute('aria-pressed',String(playing));schedule();}
  function go(p,b=0,{animate=true}={}){
    const oldPage=page, oldBeat=beat;
    page=Math.max(0,Math.min(slides.length-1,integer(p)));
    beat=Math.max(0,Math.min(maxima[page],integer(b)));
    settle();
    slides.forEach((s,i)=>{s.hidden=i!==page;s.inert=i!==page;s.classList.toggle('active',i===page);s.setAttribute('aria-hidden',String(i!==page));});
    const current=slides[page];
    current.querySelectorAll('[data-step]').forEach(el=>{
      const start=integer(el.dataset.step), end=el.hasAttribute('data-until')?integer(el.dataset.until):Infinity;
      const visible=beat>=start && beat<=end;
      el.classList.toggle('is-hidden',!visible);el.style.visibility=visible?'visible':'hidden';el.inert=!visible;el.setAttribute('aria-hidden',String(!visible));
      if(animate&&!reduced.matches&&visible&&(page!==oldPage||start>oldBeat)) animations.push(el.animate([{opacity:0,transform:'translateY(16px)'},{opacity:1,transform:'translateY(0)'}],{duration:440,easing:'ease-out'}));
    });
    if(animate&&!reduced.matches&&page!==oldPage) animations.push(current.animate([{opacity:0,transform:`translateX(${page>oldPage?32:-32}px)`},{opacity:1,transform:'translateX(0)'}],{duration:340,easing:'ease-out'}));
    $('position').textContent=`${String(page+1).padStart(2,'0')} / ${String(slides.length).padStart(2,'0')}`;
    $('step-label').textContent=`${beat+1}/${maxima[page]+1} 拍`;
    $('prev').disabled=page===0&&beat===0;$('next').disabled=isEnd();
    $('notes-text').textContent=current.querySelector('.speaker-notes')?.textContent.trim()||'本页暂无讲述备注。';
    document.querySelectorAll('[data-jump]').forEach(el=>{if(Number(el.dataset.jump)===page)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
    try{history.replaceState(null,'',`#p=${page+1}&b=${beat}`);}catch{/* Some embedded file previews restrict history. */}
    if(isEnd())setAuto(false);else schedule();fit();
  }
  function next(fromTimer=false){if(!fromTimer)setAuto(false);if(beat<maxima[page])go(page,beat+1);else if(page<slides.length-1)go(page+1);else setAuto(false);}
  function prev(){setAuto(false);if(beat>0)go(page,beat-1);else if(page>0)go(page-1,maxima[page-1]);}
  function closePanel(restore=true){$('menu').hidden=true;$('notes-panel').hidden=true;['overview','notes'].forEach(id=>$(id).setAttribute('aria-expanded','false'));if(restore&&returnFocus)returnFocus.focus();returnFocus=null;}
  function togglePanel(id,button){setAuto(false);const open=$(id).hidden;closePanel(false);if(open){returnFocus=button;$(id).hidden=false;button.setAttribute('aria-expanded','true');$(id).querySelector('button').focus();}}
  async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await $('viewport').requestFullscreen();}catch{$('player-message').hidden=false;$('player-message').textContent='当前环境不允许全屏，请使用浏览器的全屏功能。';}}
  slides.forEach((s,i)=>{const btn=document.createElement('button');btn.type='button';btn.dataset.jump=i;btn.textContent=`${String(i+1).padStart(2,'0')}  ${s.dataset.title||`第 ${i+1} 页`}`;btn.onclick=()=>{setAuto(false);go(i);closePanel();};$('page-list').append(btn);});
  $('prev').onclick=prev;$('next').onclick=()=>next();$('auto').onclick=()=>setAuto(!playing);$('full').onclick=fullscreen;
  $('overview').onclick=()=>togglePanel('menu',$('overview'));$('notes').onclick=()=>togglePanel('notes-panel',$('notes'));
  document.querySelectorAll('[data-close]').forEach(btn=>btn.onclick=()=>closePanel());
  document.addEventListener('keydown',e=>{
    if(e.ctrlKey||e.metaKey||e.altKey||e.target.closest('input,textarea,select,[contenteditable="true"]'))return;
    if(e.key==='Escape'){setAuto(false);closePanel();return;}
    const openPanel=[$('menu'),$('notes-panel')].find(el=>!el.hidden);
    if(openPanel){if(e.key==='Tab'){const items=[...openPanel.querySelectorAll('button')],first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}return;}
    if(e.target.closest('button,a')&&[' ','Enter'].includes(e.key))return;
    const key=e.key.toLowerCase();
    if(['arrowright','arrowdown',' ','arrowleft','arrowup','pagedown','pageup','home','end','f','n','p'].includes(key))e.preventDefault();
    if(['arrowright','arrowdown',' '].includes(key))next();
    else if(['arrowleft','arrowup'].includes(key))prev();
    else if(key==='pagedown'){setAuto(false);go(page+1);}
    else if(key==='pageup'){setAuto(false);go(page-1);}
    else if(key==='home'){setAuto(false);go(0);}
    else if(key==='end'){setAuto(false);go(slides.length-1,maxima.at(-1));}
    else if(key==='f')fullscreen();else if(key==='n')togglePanel('notes-panel',$('notes'));else if(key==='p')setAuto(!playing);
  });
  let touch=null;
  $('stage').addEventListener('pointerdown',e=>{if(e.pointerType==='touch')touch={x:e.clientX,y:e.clientY};});
  $('stage').addEventListener('pointerup',e=>{if(touch){const dx=e.clientX-touch.x,dy=e.clientY-touch.y;if(Math.abs(dx)>55&&Math.abs(dx)>Math.abs(dy))dx<0?next():prev();touch=null;}});
  $('stage').addEventListener('pointercancel',()=>touch=null);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)setAuto(false);});
  document.addEventListener('fullscreenchange',fit);addEventListener('resize',fit);new ResizeObserver(fit).observe($('viewport'));reduced.addEventListener('change',settle);
  function hashState(){const q=new URLSearchParams(location.hash.slice(1));setAuto(false);go(integer(q.get('p'),1)-1,integer(q.get('b')),{animate:false});}
  addEventListener('hashchange',hashState);
  window.deck={go,next:()=>next(),prev,setAuto,get state(){return{page,beat,max:maxima[page],auto:playing,total:slides.length};}};
  const q=new URLSearchParams(location.hash.slice(1));go(q.has('p')?integer(q.get('p'))-1:0,integer(q.get('b')),{animate:false});fit();
})();
