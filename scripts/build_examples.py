"""Build three visual treatments of one synthetic brief, plus the local gallery."""
import argparse
import html
import json
from pathlib import Path
from init_deck import ROOT, create

DATA = {
    'status': 'synthetic', 'topic': '读书会参与方式试验',
    'sessions': [{'label': '场次 01', 'attendees': 24, 'speakers': 8},
                 {'label': '场次 02', 'attendees': 24, 'speakers': 12},
                 {'label': '场次 03', 'attendees': 24, 'speakers': 15},
                 {'label': '场次 04', 'attendees': 24, 'speakers': 18}],
    'process': [{'label': '独立写', 'minutes': 2, 'action': '写下一句话或一个问题'},
                {'label': '两人聊', 'minutes': 8, 'action': '先让想法有一个听众'},
                {'label': '全场谈', 'minutes': 12, 'action': '自愿分享，允许跳过'},
                {'label': '留反馈', 'minutes': 3, 'action': '记录感受与未答问题'}]
}

def art(style):
    common = '<svg viewBox="0 0 560 520" role="img" aria-label="原创抽象书页与对话图形">'
    if style == 'playful':
        body = '<ellipse cx="300" cy="425" rx="215" ry="28" fill="#f9b6d9" opacity=".5"/><rect x="72" y="128" width="200" height="265" rx="28" fill="#f32991" transform="rotate(-10 172 260)"/><rect x="219" y="123" width="220" height="278" rx="24" fill="#ffc64d" transform="rotate(8 320 260)"/><path d="M295 169v170m38-160v170m38-160v170" stroke="#fffdf9" stroke-width="13"/><path d="M107 202h104m-102 35h88m-82 35h71" stroke="#fffdf9" stroke-width="13"/><circle cx="390" cy="78" r="58" fill="#211c25"/><circle cx="370" cy="78" r="7" fill="white"/><circle cx="391" cy="78" r="7" fill="white"/><circle cx="412" cy="78" r="7" fill="white"/><path d="M365 115l-10 45 46-33" fill="#211c25"/>'
    elif style == 'commerce-intelligence':
        body = '<g fill="none" stroke="#475047"><circle cx="285" cy="250" r="205"/><circle cx="285" cy="250" r="144"/><path d="M80 250h410M285 45v410"/></g><path d="M99 354V223h67v131zM200 354V167h67v187zM302 354V107h67v247zM404 354V48h67v306z" fill="#dcfa77"/><path d="M95 392h390" stroke="#acb6a9"/><circle cx="468" cy="436" r="14" fill="#eeeee5"/>'
    else:
        body = '<g fill="#24241f"><path d="M44 408h104V304h104V200h104V96h104v312z"/></g><path d="M69 432h412M122 330h71M226 227h71M331 123h71" stroke="#c6c4bb" stroke-width="2"/><path d="M294 180l91-43 92 22v172l-92-21-91 42z" fill="#e75035"/><path d="M385 137v173m-64-111 45-22m-45 53 45-22m37-25 49 12m-49 20 49 12" stroke="#f1efe8" stroke-width="6"/>'
    return '<div class="art">' + common + body + '</svg></div>'

def slides(style, data):
    last = data['sessions'][-1]
    percentage = last['speakers'] / last['attendees'] * 100
    counts = '、'.join(str(s['speakers']) for s in data['sessions'])
    denominators = '、'.join(str(s['attendees']) for s in data['sessions'])
    bars = ''.join(f'<div class="bar-row reveal" data-step="{i+1}"><span>{html.escape(s["label"])}</span><div class="track"><div class="bar" style="--value:{s["speakers"]/s["attendees"]*100:.6f}%"></div></div><span class="bar-label">{s["speakers"]} / {s["attendees"]} 人</span></div>' for i,s in enumerate(data['sessions']))
    steps = ''.join(f'<div class="step reveal" data-step="{i+1}"><div class="time">{s["minutes"]}<small>分钟</small></div><h3>{html.escape(s["label"])}</h3><p>{html.escape(s["action"])}</p></div>' for i,s in enumerate(data['process']))
    total = sum(s['minutes'] for s in data['process'])
    foot = '<div class="source">模拟活动方案 · 数据及安排均为示例，不代表真实成效</div>'
    return f'''
<section class="slide hero" data-title="让每个人都有话可说">
 <div class="eyebrow">READING TOGETHER / 活动方案</div>
 <h1>让每个人<br>都有话可说</h1>
 <p class="subtitle">一场读书会，从听别人分享，<br>到让自己的想法被听见。</p>
 {art(style)}<div class="hero-tag reveal" data-step="1">24 人 · {total} 分钟讨论单元 · 一次小规模试验</div>
 {foot}<aside class="speaker-notes">这是用于检验 Skill 的新主题模拟方案。目标是让表达入口更容易，而不是要求每个人必须发言。后面的数字全部是模拟数据。</aside>
</section>
<section class="slide statement" data-title="先写，再说">
 <div class="eyebrow">01 / 表达入口</div><div class="big-index" aria-hidden="true">01</div>
 <div class="big-phrase">先写，再说。</div>
 <div class="statement-grid">
  <div class="reveal" data-step="1"><h3>直接问全场</h3><p>“谁来分享一下？”<br>先开口的人，需要同时组织和表达。</p></div>
  <div class="reveal" data-step="2"><h3>给一个准备动作</h3><p>先写一句，再和身边的人说。<br>最后自愿向全场分享。</p></div>
 </div>{foot}<aside class="speaker-notes">这是待尝试的活动设计假设，不宣称已证明有效。保留参与者跳过的自由，不用发言次数评价个人。</aside>
</section>
<section class="slide evidence" data-title="数字记录参与，不解释原因">
 <div class="eyebrow">02 / 观察指标</div><h2>记录参与，暂不解释原因</h2>
 <div class="evidence-grid"><div class="stat"><div class="value">{last['speakers']}</div><div class="unit">/ {last['attendees']} 人</div><div class="caption">第 4 场模拟发言人数<br>参与比例 {percentage:.1f}%</div></div>
 <div><div class="bars">{bars}</div><div class="axis-note">条宽：0—100% · 发言人数 ÷ 当场到场人数</div></div></div>
 <div class="evidence-note">人数增加 ≠ 设计已被证明有效。还要听参与者的感受。</div>
 {foot}<aside class="speaker-notes">四场发言人数分别为 {counts} 人，到场人数依次为 {denominators} 人。仅演示统计口径与可视化，没有对照组或真实试验，不推断因果。发言人数按每场去重的人数统计。</aside>
</section>
<section class="slide ledger" data-title="选择一种低压力的起点">
 <div class="eyebrow">03 / 方式比较</div><h2>先让表达容易发生</h2><p class="subtitle">这次建议从两人交流开始，再回到全场。</p>
 <table><thead><tr><th>方式</th><th>适合的时刻</th><th>需要留意</th></tr></thead><tbody>
 <tr class="reveal" data-step="1"><td>全场自由谈</td><td>大家已有准备，愿意直接回应</td><td>留出等待，避免少数人包办</td></tr>
 <tr class="selected reveal" data-step="2"><td>两人先聊<span class="tag">本次建议试用</span></td><td>刚读完，需要先整理自己的想法</td><td>分配时间，允许只听不说</td></tr>
 <tr class="reveal" data-step="3"><td>匿名问题纸</td><td>有疑问，但暂时不想公开表达</td><td>说明回应方式，不追问身份</td></tr>
 </tbody></table>{foot}<aside class="speaker-notes">这张表是方案判断，不是排名或量化研究结论。根据现场熟悉程度选择方法，不把一种形式强加给所有活动。</aside>
</section>
<section class="slide sequence" data-title="用 25 分钟跑一次小试验">
 <div class="eyebrow">04 / 现场节奏</div><h2>用 {total} 分钟，跑一次小试验</h2><p class="subtitle">四步有顺序，时间可以按现场调整。</p>
 <div class="steps">{steps}</div>{foot}<aside class="speaker-notes">时间依次为 2、8、12、3 分钟，合计 25 分钟。节点宽度不表示时长比例。主持人提醒剩余时间，但不强迫参与者发言。</aside>
</section>
<section class="slide closing" data-title="下一次，只验证一件事">
 <div class="eyebrow">05 / 下一步</div><div class="signature">TRY · OBSERVE · ADJUST</div>
 <h1>下一次，<br>只验证一件事。</h1>
 <div class="next-action"><div class="reveal" data-step="1"><h3>尝试</h3><p>把直接全场分享，<br>改为“先写，再两人聊”。</p></div><div class="reveal" data-step="2"><h3>观察</h3><p>记录去重发言人数，<br>再问一句：这样更容易开口吗？</p></div></div>
 {foot}<aside class="speaker-notes">先做一次可撤回的小试验。记录事实与主观反馈，下一次再调整。这里没有已实现的参与率提升承诺。</aside>
</section>'''

def build(base):
    folders = {'playful':'playful','commerce-intelligence':'commerce-intelligence','project-journal':'reading-circle'}
    for style, folder in folders.items():
        out=create(base/'examples'/folder,style,'让每个人都有话可说')
        text=(out/'index.html').read_text(encoding='utf-8')
        a,b=text.split('<!-- SLIDES:START -->',1)
        _,c=b.split('<!-- SLIDES:END -->',1)
        (out/'index.html').write_text(a+'<!-- SLIDES:START -->\n'+slides(style,DATA)+'\n<!-- SLIDES:END -->'+c,encoding='utf-8')
        (out/'data.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (out/'sources.md').write_text('# 来源与素材\n\n全部为新写的模拟活动方案。data.json 是唯一数据输入快照；没有真实参与者、访谈或业绩。\n\n图形为本包原创 SVG，非现场照片，无外部素材。采用系统完整字体回退，无裁切字体、无 CDN。\n\n假设：准备时间和两人交流可能降低表达门槛，尚未做活动实测。四场模拟数值不支持因果解释。\n',encoding='utf-8')
        (out/'outline.md').write_text('# 逐页内容与口径\n\n1. 让每个人都有话可说：交代 24 人模拟活动与参与目标。\n2. 先写再说：提出低压力的准备动作，保留跳过自由。\n3. 记录参与：4 场模拟发言人数 8/12/15/18，各场 24 人；第 4 场 75.0%。不能解释因果。\n4. 选择方式：全场、两人、匿名纸条三种方式的取舍。\n5. 现场节奏：2+8+12+3=25 分钟，节点宽度不代表时间。\n6. 下一步：只试一种改变，记录人数和主观反馈。\n\n每页详细讲述备注见 index.html 的 speaker-notes。\n',encoding='utf-8')
        design=(out/'DESIGN.md').read_text(encoding='utf-8').replace('待填：观众、页数、取舍与复杂页设计。','受众：活动组织者。六页，约五分钟讲解。无图像生成依赖；用原创 SVG 建立书页/对话关系。\n复杂页：四组条形图、三行方式对账、四步现场节奏。所有数据为模拟，页面均显示边界。\n字体：完整系统字体回退，具体设备字形可能不同。长标题通过断行处理。')
        (out/'DESIGN.md').write_text(design,encoding='utf-8')
        (out/'README.md').write_text('# 让每个人都有话可说\n\n打开 index.html。6 页模拟读书会方案，含原创图形、4 组数据、方式比较、4 步流程。\n\n←/→ 逐拍，PageUp/PageDown 翻页；N 备注，F 全屏，P 播放，Esc 暂停。\n\ndata.json 保存数据；outline.md 保存口径。更新数据必须同时重建图表并复核结论，修改 JSON 不会在浏览器中自动刷新。\n\n不代表实际活动效果，HTML 并非 PPTX。系统字体跨设备需复核。\n',encoding='utf-8')
    print('Built 3 treatments of one new topic, 18 pages total.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root',type=Path,default=ROOT,help='Fresh output root; existing example directories are not overwritten')
    args=parser.parse_args(); build(args.output_root.resolve())

if __name__=='__main__': main()
