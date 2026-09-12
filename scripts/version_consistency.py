r"""检查各版本规则纸共享段落与网页数据共享键一致；纯标准库，CI 兜底。

tex 共享段 = 从 `\shead{一}` 行起、至底部小字行（`{\fontsize{9}{12}`）前的全部
内容，覆盖奖级表、状元表、异常与收尾、记录栏。标题区与底部小字是版本自有内容。
site-data.json 共享键 = 各版本必须一致的规则性文案（骰面、判定条件、比较键、
步骤文字）；版本差异只允许出现在 SHARED_JSON_KEYS 之外的键。
发现任何不一致即非零退出——改共享内容必须同步所有版本。
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
START = '\\shead{一}'
END = '{\\fontsize{9}{12}'
SHARED_JSON_KEYS = [
    ('overview', 'route'),
    ('start', 'subheading'),
    ('start', 'steps'),
    ('prizes', 'items'),
    ('prizes', 'workedExample'),
    ('champion', 'ranks'),
    ('ending', 'steps'),
    ('questions', 'exceptions'),
]


def shared_lines(tex):
    lines = tex.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(START))
    end = next(i for i, l in enumerate(lines) if l.startswith(END))
    return lines[start:end]


def json_at(data, path):
    value = data
    for key in path:
        value = value[key]
    return value


def main():
    ok = True
    papers = sorted((ROOT / 'versions').glob('*/rules-paper.tex'))
    sections = {p.parent.name: shared_lines(p.read_text(encoding='utf-8')) for p in papers}
    names = sorted(sections)
    if len(names) >= 2:
        base = names[0]
        for name in names[1:]:
            a, b = sections[base], sections[name]
            if a == b:
                print(f'PASS tex 共享段一致：{base} = {name}（{len(a)} 行）')
                continue
            ok = False
            diff = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            print(f'FAIL tex 共享段不一致：{base} vs {name}，自第 {diff + 1} 行起不同（{len(a)} 行 vs {len(b)} 行）')
            for label, lines in ((base, a), (name, b)):
                if diff < len(lines):
                    print(f'  {label}: {lines[diff]}')
    else:
        print(f'PASS tex 共享段一致：当前 {len(names)} 个版本，暂无可比对对象')

    datas = {}
    for name in names:
        path = ROOT / 'versions' / name / 'site-data.json'
        if path.exists():
            datas[name] = json.loads(path.read_text(encoding='utf-8'))
    if len(datas) >= 2:
        keys = sorted(datas)
        base = keys[0]
        for name in keys[1:]:
            for path in SHARED_JSON_KEYS:
                a, b = json_at(datas[base], path), json_at(datas[name], path)
                if a == b:
                    continue
                ok = False
                print(f'FAIL site-data 共享键不一致：{base} vs {name}，键 {".".join(path)}')
    else:
        print(f'PASS site-data 共享键一致：当前 {len(datas)} 份数据，暂无可比对对象')

    if not ok:
        raise SystemExit('共享内容不一致：改共享规则必须同步所有版本（见 AGENTS.md 四件套）')


if __name__ == '__main__':
    main()
