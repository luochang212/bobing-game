"""检查交付 PDF、渲染预览并解码二维码；先运行 make pdf。

依赖：Poppler 命令行工具，以及 pillow、zxing-cpp。安装与使用见 README。
二维码本身由 TeX 的 qrcode 宏包生成，本脚本不修改 PDF。
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image
import zxingcpp


ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = 'output/pdf/rules-paper.pdf'
# 2026-09 文件名英文化前的旧交付路径；--compare-ref 对照历史提交时回退使用。
LEGACY_PDF_PATH = 'output/pdf/博饼规则-A4黑白.pdf'


def git_show_pdf(ref):
    for path in (PDF_PATH, LEGACY_PDF_PATH):
        result = subprocess.run(['git', 'show', f'{ref}:{path}'], cwd=ROOT,
                                capture_output=True)
        if result.returncode == 0:
            return result.stdout
    raise ValueError(f'{ref} 中既无 {PDF_PATH} 也无旧路径 {LEGACY_PDF_PATH}')


def pdf_text(pdf):
    return subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, default=ROOT / PDF_PATH)
    parser.add_argument('--url', default='https://www.luochang.ink/bobing-game/',
                        help='二维码应解出的完整地址')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'tmp/pdf-review')
    parser.add_argument('--preview-output', type=Path,
                        help='全部检查通过后，将 150 DPI 预览复制到此 PNG 路径')
    parser.add_argument('--compare-ref',
                        help='纯排版修改时，额外与指定 Git 版本的交付 PDF 对照正文')
    args = parser.parse_args()
    if args.preview_output and args.preview_output.suffix.lower() != '.png':
        parser.error('--preview-output 必须是 .png 路径')

    bbox = subprocess.check_output(['pdftotext', '-bbox', str(args.pdf), '-'])
    document = ET.fromstring(bbox)
    pages = document.findall('.//{*}page')
    if len(pages) != 1:
        raise ValueError(f'交付 PDF 必须为一页，实际为 {len(pages)} 页')
    words = document.findall('.//{*}word')
    if not words:
        raise ValueError('PDF 未提取到规则文字')
    ymax = max(float(word.attrib['yMax']) for word in words)
    if ymax > 806:
        raise ValueError(f'内容最低点 {ymax:.3f}pt 超过 806pt 安全线')
    print(f'PASS 单页与版面：1 页，yMax = {ymax:.3f}pt')

    args.output_dir.mkdir(parents=True, exist_ok=True)
    text = pdf_text(args.pdf)
    (args.output_dir / 'rules.txt').write_text(text, encoding='utf-8')
    for dpi in (100, 150, 300):
        prefix = args.output_dir / f'rules-{dpi}'
        subprocess.run(['pdftoppm', '-r', str(dpi), '-singlefile', '-png',
                        str(args.pdf), str(prefix)], check=True)
        with Image.open(prefix.with_suffix('.png')) as page:
            codes = zxingcpp.read_barcodes(page)
        decoded = [code.text for code in codes]
        if decoded != [args.url]:
            raise ValueError(f'{dpi} DPI 二维码解码不符：{decoded!r}')
        print(f'PASS {dpi} DPI 整页二维码：{decoded[0]}')

    if args.compare_ref:
        before = git_show_pdf(args.compare_ref)
        before_text = subprocess.check_output(
            ['pdftotext', '-layout', '-', '-'], input=before).decode('utf-8')
        # 忽略排版换行、章节序号顿号和新增的扫码标签，保留规则文字与数字。
        def normalize(value):
            return re.sub(r'[\s、]', '', value.replace('扫码看规则', ''))
        if normalize(before_text) != normalize(text):
            raise ValueError('与指定 Git 版本的规则正文不一致，请检查文字差异')
        print(f'PASS 规则正文与 {args.compare_ref} 一致')

    if args.preview_output:
        args.preview_output.parent.mkdir(parents=True, exist_ok=True)
        source = args.output_dir / 'rules-150.png'
        if source.resolve() != args.preview_output.resolve():
            shutil.copyfile(source, args.preview_output)
        print(f'预览已更新：{args.preview_output}')
    print(f'渲染图片与提取文字：{args.output_dir}')


if __name__ == '__main__':
    main()
