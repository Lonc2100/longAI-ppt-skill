"""Create a portable HTML deck in a new/empty directory. No network, no deletion."""
import argparse
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def catalog():
    return json.loads((ROOT / 'designs/catalog.json').read_text(encoding='utf-8'))

def resource(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError('Resource must be an existing file inside the skill package')
    return path

def create(output, style, title):
    choice = next((item for item in catalog() if item['id'] == style), None)
    if choice is None:
        raise ValueError('Unknown style; use --help to list styles')
    output = Path(output).resolve()
    if output == ROOT or output.is_relative_to(ROOT / 'templates') or output.is_relative_to(ROOT / 'designs'):
        raise ValueError('Output may not overwrite skill resources')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise FileExistsError('Output is not empty; choose a new version directory')
    template = resource('templates/deck.html').read_text(encoding='utf-8')
    design = resource(choice['design']).read_text(encoding='utf-8')
    # Strip the package-relative sample link in a standalone project copy.
    design = '\n'.join(line for line in design.splitlines() if not line.startswith('[查看实际样张]'))
    output.mkdir(parents=True, exist_ok=True)
    for name in ('base.css', 'player.js'):
        shutil.copyfile(resource('templates/' + name), output / name)
    shutil.copyfile(resource(choice['css']), output / 'theme.css')
    (output / 'index.html').write_text(template.replace('{{TITLE}}', html.escape(title)).replace('{{STYLE}}', html.escape(style)), encoding='utf-8')
    (output / 'custom.css').write_text('/* Project-specific compositions; preserve the shared player contract. */\n', encoding='utf-8')
    (output / 'DESIGN.md').write_text(f'# 本次项目：{title}\n\n风格：{style}。输出：1600×900 HTML。\n\n待填：观众、页数、取舍与复杂页设计。\n\n---\n\n{design}\n', encoding='utf-8')
    (output / 'outline.md').write_text('# 逐页内容\n\n待填：页码、观众问题、核心回答、证据、上屏内容、讲述备注。\n', encoding='utf-8')
    (output / 'sources.md').write_text('# 来源与素材\n\n待填：来源、归属、日期、事实/假设/模拟状态。无外部图片时明确记录。\n', encoding='utf-8')
    (output / 'README.md').write_text(f'# {title}\n\n打开 index.html，完整保留同目录 CSS/JS 与素材。HTML 演示稿，无 PPTX 导出。\n\n方向键逐拍；PageUp/PageDown 翻页；N 备注；F 全屏；P 自动播放；Esc 暂停。\n\n这是初始化起步稿，替换待填项并检查后再交付。系统字体在不同设备可能变化。\n', encoding='utf-8')
    return output

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--style', choices=[x['id'] for x in catalog()], default='project-journal')
    parser.add_argument('--title', required=True)
    args = parser.parse_args()
    try:
        path = create(args.output, args.style, args.title)
    except (ValueError, FileExistsError) as exc:
        parser.exit(2, f'{exc}\n')
    print(f'Created: {path}')

if __name__ == '__main__':
    main()
