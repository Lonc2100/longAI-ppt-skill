# Design Deck

给 AI 一份主题、文档或数据，先确认页数与 ASCII 逐页内容，再研究设计和素材，交付可离线播放的演示稿。

当前本地流程已按用户反馈修订：总页数、每页主标题及全部必现文字须先得到用户确认，才进入视觉研究。0.1.0 示例的视觉水准未获用户认可，保留作功能原型；0.1.0 ZIP 是此前快照。0.2.0 增加独立编辑器与文字可编辑的 PPTX 导出。

已确认的制作顺序：材料 → 页数与 ASCII 逐页文字确认 → Refero／实际作品参考 → 主方向 → DESIGN.md 初稿 → Pinterest 找方向并回源获取素材／免费图库／已有素材／必要生图 → 实际素材代表页与参考对照 → 更新定版同一 DESIGN.md → 全稿 → 检查交付。完整字段见 [DESIGN.md 规范](design-contract.md)。

**先打开 [风格选款页](../gallery/index.html)**，再看 [完整案例：让每个人都有话可说](../examples/reading-circle/index.html)。三种风格都附六页实际页面，可以翻页比较，不只有封面。

## 包里有什么

- 一个主 Skill，覆盖材料理解、页数和 ASCII 逐页文字确认、视觉/素材研究、代表页、制作、检查与局部修改。
- 趣味立体、商业情报、建筑编辑三套 DESIGN.md，各自有构图与适用边界。
- 无框架的播放器：逐拍推进、回退、跳页、备注、自动播放、全屏、减少动态效果。
- 独立编辑器：点字输入、替换照片、调裁切、撤销重做、单文件保存与修改记录。
- 标准库初始化脚本、静态检查、可选浏览器检查，以及可移动交付包。

成品是 **可编辑 HTML 演示稿**，用浏览器打开即可直接改字、换图并保存。支持导出真正的 PPTX：文字为原生文本框，照片与装饰合成背景；动画保留在 HTML。不是所有对象都能在 PowerPoint 中独立编辑。

## 安装与开始

解压后把整个 `design-deck` 文件夹放进所用 AI 工具配置的 Skills 目录，保留根部唯一的 `SKILL.md`。也可以在支持本地文件读取的编程助手中明确要求读取该文件。不同工具的自动发现/启用方式由该工具决定；本包不自动更改配置。

当前交付是本地 ZIP，尚未发布仓库，因此不提供虚构的 `npx skills add` 远程安装地址。

你可以直接这样说：

> 用 design-deck 把这份材料做成 8 页 HTML 演示稿，给新同事讲解。先让我确认 ASCII 逐页标题和必现文字，再找适合的视觉参考。

> 按建筑编辑风做一份项目汇报。材料和日期以我提供的表格为准；先确认页数和逐页文字，再制定设计初稿、找素材，制作封面和风险代表页。

> 这套演示稿第三页字太多，保留事实，拆成两页并检查播放。

制作助手需要本地读写能力；脚本初始化需要 Python 3.10+。生成可编辑单文件另需 beautifulsoup4；可选本地自动保存服务需 Python。成品播放、编辑、下载和 PPTX 导出不需要 Python、Node、联网或 AI 账号。生图不是必需条件。浏览器自动检查另需 Playwright 和受支持的 Chromium 浏览器。

## 手动初始化

在技能目录运行（路径有空格请加引号；也可用脚本绝对路径从别处运行）：

```text
python scripts/init_deck.py "my-deck" --style project-journal --title "我的项目汇报"
python scripts/check_deck.py "my-deck"
python scripts/verify_browser.py "my-deck" --browser "/path/to/chrome"
python scripts/enable_editor.py "my-deck" "my-deck-editable"
python scripts/validate_skill.py .
```

风格 ID：`playful`、`commerce-intelligence`、`project-journal`。初始化后的一页起步稿明确含待填项，不能直接交付为成品；静态检查会提示它们。

快捷键：左右方向键逐拍、PageUp/PageDown 翻页、Home/End 首末状态、N 备注、F 全屏、P 播放/暂停、Esc 暂停并关闭面板。触屏可左右滑动，按钮始终可访问。

## 如何扩展设计库

按 [风格契约](design-contract.md) 增加独立文件夹，配 DESIGN.md、theme.css 和真实样张；登记到 `designs/catalog.json`。复用播放器，重做适合新风格的页面构图；不能只换色后宣称新风格。用 [质量检查](quality.md) 验证后再标为可用。

## 验证与当前限制

初版历史证据见 [交付记录](../reports/creation-handoff.md)，0.2.0 编辑与导出证据见 [编辑器验证](../reports/editor-validation.md)。脚本和浏览器检查只能证明所测文件及机制，不能证明所有模型会正确执行 Skill，也不能替代用户审美评价。

系统字体按设备回退；跨系统排版需复核。需要固定字体时自行打包可分发字体并保留许可；不要复用只包含旧稿文字的字体子集。发布包未携带原案例的 IP 角色、摄影、商业项目或私密记录。

## Troubleshooting

- **字形不同或方框**：在系统安装支持该语言的字体，或合法打包完整字体；新稿需重验排版。
- **只看到第一页**：打开整个文件夹中的 `index.html`，保留 CSS/JS 相对路径；用浏览器而不是禁用 JS 的文档预览器。
- **Python/Playwright 不可用**：可人工复制模板并编辑；浏览器检查按质量清单手动完成，不声称自动检查通过。
- **无法全屏**：使用浏览器全屏功能；播放器会显示失败提示。
- **目标目录已存在**：选择新版本目录。脚本拒绝覆盖，旧版保留。
- **要交 .pptx**：在可编辑稿中点“导出 PowerPoint”。原生文字可编辑；照片、渐变、装饰是背景，见 [编辑与导出范围](editing.md)。
- **改完字重新打开没变化**：浏览器草稿不等于原文件；点保存或下载 HTML，或者使用附带的本地编辑服务自动回写。

代码与原创模板按 [MIT LICENSE](../LICENSE) 使用。第三方方法来源与取舍见 [参考研究](../reports/prior-art-research.md)；没有复制参考 Skill 的受限代码或素材。
