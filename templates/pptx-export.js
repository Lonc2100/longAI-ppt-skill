/* Native text over a rendered background. Independent browser export adapter. */
(() => {
  'use strict';
  const wait=ms=>new Promise(r=>setTimeout(r,ms));
  const color=s=>{const parts=s.match(/[\d.]+/g);return parts?parts.slice(0,3).map(x=>Math.round(Number(x)).toString(16).padStart(2,'0')).join(''):'FFFFFF';};
  // Use browser line breaks and text geometry instead of guessing Chinese wrapping.
  function textLines(slide){
    const origin=slide.getBoundingClientRect(),out=[];
    for(const node of slide.querySelectorAll('[data-edit-id]')){
      if(!node.textContent.trim())continue;const css=getComputedStyle(node);if(css.visibility==='hidden'||css.display==='none')continue;
      const walker=document.createTreeWalker(node,NodeFilter.SHOW_TEXT);let t;let rows=[];
      while(t=walker.nextNode()){
        let offset=0;
        for(const c of t.textContent){const range=document.createRange();range.setStart(t,offset);range.setEnd(t,offset+c.length);offset+=c.length;const r=range.getBoundingClientRect();if(!r.height)continue;
          let row=rows.at(-1);if(!row||Math.abs(row.top-r.top)>3){row={text:'',left:r.left,right:r.right,top:r.top,bottom:r.bottom};rows.push(row);}row.text+=c;row.right=Math.max(row.right,r.right);row.bottom=Math.max(row.bottom,r.bottom);
        }
      }
      for(const r of rows){if(!r.text.trim())continue;const font=parseFloat(css.fontSize);out.push({text:r.text,options:{x:(r.left-origin.left)/100,y:(r.top-origin.top)/100,w:(r.right-r.left+10)/100,h:(r.bottom-r.top+5)/100,fontFace:css.fontFamily.split(',')[0].replace(/["']/g,''),fontSize:font*.72,color:color(css.color),bold:Number(css.fontWeight)>=600,italic:css.fontStyle==='italic',charSpacing:(parseFloat(css.letterSpacing)||0)*.72,margin:0,breakLine:false,wrap:false,valign:'mid',paraSpaceAfter:0,paraSpaceBefore:0,lang:'zh-CN',transparency:Math.round((1-Number(css.opacity))*100)}});}
    }
    return out;
  }
  async function exportPptx(){
    if(!window.PptxGenJS||!window.html2canvas)throw new Error('导出组件缺失，请使用完整的可编辑HTML。');
    const saved=window.deck.state,wasEditing=window.designDeckEditor.editing;window.deck.setAuto(false);
    const overlay=document.createElement('div');overlay.id='dd-export-progress';overlay.setAttribute('role','status');document.body.append(overlay);
    document.body.classList.add('dd-export');
    const ppt=new PptxGenJS();ppt.defineLayout({name:'DESIGN_DECK',width:16,height:9});ppt.layout='DESIGN_DECK';ppt.author='Design Deck';ppt.subject='文字可编辑；摄影与装饰合成背景。HTML动画不转换。';ppt.title=document.title;ppt.lang='zh-CN';ppt.theme={headFontFace:'Microsoft YaHei',bodyFontFace:'Microsoft YaHei',lang:'zh-CN'};
    const slides=[...document.querySelectorAll('.slide')],metrics=[];
    try{
      await document.fonts.ready;
      for(let i=0;i<slides.length;i++){
        overlay.textContent=`正在导出 PowerPoint · ${i+1} / ${slides.length}`;window.deck.go(i,999,{animate:false});
        const slide=slides[i];slide.querySelectorAll('[data-step]').forEach(n=>{n.style.visibility='visible';n.style.opacity='1';});
        await Promise.all([...slide.querySelectorAll('img')].map(img=>img.decode()));await wait(60);
        const lines=textLines(slide);
        // html2canvas substitutes custom tags and drops their data attributes.
        // Hide native text before cloning so its inline opacity survives that substitution.
        const hidden=[...slide.querySelectorAll('[data-edit-id]')].map(n=>[n,n.style.opacity]);
        hidden.forEach(([n])=>n.style.opacity='0');
        let canvas;
        try{canvas=await html2canvas(slide,{backgroundColor:null,scale:1,width:1600,height:900,windowWidth:1600,windowHeight:900,logging:false,useCORS:false,allowTaint:false,onclone:doc=>{
          doc.querySelectorAll('.dd-selected-image').forEach(n=>n.classList.remove('dd-selected-image'));
        }});}finally{hidden.forEach(([n,value])=>n.style.opacity=value);}
        const s=ppt.addSlide();s.addImage({data:canvas.toDataURL('image/png'),x:0,y:0,w:16,h:9});
        for(const line of lines)s.addText(line.text,line.options);
        s.addNotes((slide.querySelector('.speaker-notes')?.textContent||'')+'\n导出说明：原生文字框可编辑；照片、渐变和装饰合成背景；不含HTML分拍动画。');
        metrics.push({page:i+1,textBoxes:lines.length,text:lines.map(x=>x.text).join('')});
      }
      const blob=await ppt.write({outputType:'blob',compression:true});
      window.designDeckEditor.download(blob,document.title.replace(/[\\/:*?"<>|]/g,'_')+'_文字可编辑.pptx');window.designDeckPptx.lastExport={pages:slides.length,metrics,bytes:blob.size};
      return window.designDeckPptx.lastExport;
    }finally{
      document.body.classList.remove('dd-export');overlay.remove();window.deck.go(saved.page,saved.beat,{animate:false});dispatchEvent(new Event('resize'));
      if(wasEditing)document.body.classList.add('dd-edit');
    }
  }
  window.designDeckPptx={export:exportPptx,textLines};
})();
