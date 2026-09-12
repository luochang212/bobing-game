r"""检查各版本规则纸共享段落一致；纯标准库，CI 兜底。

共享段 = 从 `\shead{一}` 行起、至底部小字行（`{\fontsize{9}{12}`）前的全部内容，
覆盖奖级表、状元表、异常与收尾、记录栏。标题区与底部小字是版本自有内容，
不参与比对。发现任何不一致即非零退出——改共享规则必须同步所有版本。
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
START = '\\shead{一}'
END = '{\\fontsize{9}{12}'


def shared_lines(tex):
    lines = tex.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(START))
    end = next(i for i, l in enumerate(lines) if l.startswith(END))
    return lines[start:end]


def main():
    papers = sorted((ROOT / 'versions').glob('*/rules-paper.tex'))
    if len(papers) < 2:
        print(f'PASS 共享段一致：当前 {len(papers)} 个版本，暂无可比对对象')
        return
    sections = {p.parent.name: shared_lines(p.read_text(encoding='utf-8')) for p in papers}
    names = sorted(sections)
    base = names[0]
    ok = True
    for name in names[1:]:
        a, b = sections[base], sections[name]
        if a == b:
            print(f'PASS 共享段一致：{base} = {name}（{len(a)} 行）')
            continue
        ok = False
        diff = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        print(f'FAIL 共享段不一致：{base} vs {name}，自第 {diff + 1} 行起不同（{len(a)} 行 vs {len(b)} 行）')
        for label, lines in ((base, a), (name, b)):
            if diff < len(lines):
                print(f'  {label}: {lines[diff]}')
    if not ok:
        raise SystemExit('共享段不一致：改共享规则必须同步所有版本（见 AGENTS.md 四件套）')


if __name__ == '__main__':
    main()
