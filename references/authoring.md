# 制作接口

所有文件使用 UTF-8；路径相对交付文件夹。播放器是独立小底座，不依赖 npm、框架、服务器或其他 Skill。

页数与 ASCII 逐页文字确认后，先选主参考，再形成本项目 DESIGN.md 初稿。若使用初始化脚本，应在写初稿前运行一次，随后搜集素材、制作代表页、更新同一规范并定版；不要在已有初稿目录再次运行初始化器。复制来的主题只是起点，不能覆盖项目取舍。

## 页面

在 index.html 的 `SLIDES:START` / `SLIDES:END` 注释之间放任意数量的页面：

```html
<section class="slide" data-title="观众能理解的页名" data-delay="6000">
  <div class="eyebrow">章节 / 01</div>
  <h1>本页的核心回答</h1>
  <div class="reveal" data-step="1">下一拍出现的证据</div>
  <div class="reveal" data-step="2" data-until="3">第 2—3 拍显示</div>
  <aside class="speaker-notes">只给讲述者看的备注。</aside>
</section>
```

`data-step` 是非负整数，底座推导每页最大分拍；不写表示一开始出现。`data-until` 可省略，表示一直显示。每页不宜堆太多分拍；全页最终状态必须可读。`data-delay` 为自动播放每拍等待毫秒，最短 1000。页面不需要固定页数或改 JS。

页目、备注、键盘与触屏由 player.js 接管。非当前页和隐藏分拍会从焦点与可访问树中移出。`#p=2&b=1` 指第二页第二个状态（拍号从 0 起）。底座提供 `window.deck.go(page, beat)`、`next()`、`prev()`、`setAuto(bool)` 和只读 state；page 从 0 起。

## 排版

固定 1600×900 舞台按窗口等比缩放，不重新流排。它适合演示；手机上的长文本阅读需另行设计。播放器工具条不遮挡正文安全区。

`base.css` 只定义舞台、控制、基础布局；`theme.css` 来自风格库；`custom.css` 定义本次项目构图。选择 hero / statement / evidence / ledger / sequence / closing 只是起点，可以按内容创建新的 CSS 布局，不能把所有页固定为列表。

系统中文字体回退：Noto Sans SC → Microsoft YaHei → PingFang SC → sans-serif。字体缺失时重新检查标题换行与表格；必要时合法打包字体，不复制项目专用子集假装完整覆盖。

## 图片与图形

运行时资源全部本地。SVG 只用自己创建或可信素材，未经检查的外来 SVG/HTML 不直接执行。图注区分主题配图、真实现场和数据图。图片设置 alt；纯装饰设 aria-hidden。

没有生图能力：趣味风用原创几何物件、气泡和排字；商业风用数字与证据图；编辑风用结构线、裁切色面和信息对账。原案例的角色与摄影不打包。

## 维护

改某页只修改相应 section、备注和样式；复制旧版本再改。改数据必须同步标题和图表。改页数后播放器自动适配，仍需检查首末边界和跳页。
