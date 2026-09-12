r"""检查各版本规则纸与网页数据的共享内容一致；纯标准库，CI 兜底。

规则族：各版本 README 的"规则族："行声明归属（缺省为版本目录名）。
- 同族版本：整段比对——从 `\shead{一}` 行起、至底部小字行（`{\fontsize{9}{12}`）
  前的全部内容，覆盖奖级表、状元表、异常与收尾、记录栏。
- 跨族版本：只比对共识块——各规则模型都必须逐字相同的段落（第一节流程、
  第三节状元比较、出碗与叠骰行）。奖品模型允许不同，故第二节奖级表与
  结束条款不跨族比对。
site-data.json：按 SHARED_JSON_KEYS 比对各版本必须一致的规则性文案；
prizes.items 只比对 (id, faces, condition)（stock 标签随奖品模型合法不同）。
发现任何不一致即非零退出——改共享内容必须同步对应版本。
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
START = '\\shead{一}'
END = '{\\fontsize{9}{12}'
CONSENSUS = [
    ('第一节流程', '\\shead{一}', '\\shead{二}'),
    ('第三节状元比较', '\\shead{三}', '\\shead{四}'),
    ('出碗与叠骰行', '\\textbf{出碗：}', None),
]
JSON_CORE_KEYS = [   # 跨族必须一致：判定与比较的语义核心
    ('start', 'subheading'),
    ('prizes', 'items'),
    ('prizes', 'workedExample'),
    ('champion', 'ranks'),
    ('questions', 'exceptions'),
]
JSON_FAMILY_KEYS = [   # 同族一致：随奖品模型措辞可能不同
    ('overview', 'route'),
    ('start', 'steps'),
    ('prizes', 'callout'),
    ('ending', 'steps'),
]


def shared_lines(tex):
    lines = tex.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(START))
    end = next(i for i, l in enumerate(lines) if l.startswith(END))
    return lines[start:end]


def block_lines(lines, start_anchor, end_anchor):
    start = next(i for i, l in enumerate(lines) if l.startswith(start_anchor))
    if end_anchor is None:
        return [lines[start]]
    end = next(i for i, l in enumerate(lines) if l.startswith(end_anchor))
    return lines[start:end]


def json_at(data, path):
    value = data
    for key in path:
        value = value[key]
    return value


def normalize_json(path, value):
    """抽取跨版本必须一致的语义字段；奖品库存标签等表现性字段不参与。"""
    if path == ('prizes', 'items'):
        return [(item['id'], tuple(item['faces']), item['condition']) for item in value]
    if path == ('prizes', 'workedExample'):
        return tuple(value['faces'])
    return value


def zhuangyuan_table(tex):
    r"""抽取状元等级表（\begin{tabularx} 起、表头含"状元等级"、至 \end{tabularx}）。"""
    lines = tex.splitlines()
    for i, l in enumerate(lines):
        if l.startswith('\\begin{tabularx}') and any(
                '状元等级' in lines[j] for j in range(i + 1, min(i + 4, len(lines)))):
            end = next(j for j in range(i, len(lines)) if lines[j].startswith('\\end{tabularx}'))
            return lines[i:end + 1]
    raise ValueError('未找到状元等级表')


def family_of(version_dir):
    readme = version_dir / 'README.md'
    match = re.search(r'^规则族：([A-Za-z0-9_-]+)', readme.read_text(encoding='utf-8'), re.M) if readme.exists() else None
    return match.group(1) if match else version_dir.name


def main():
    ok = True
    papers = sorted((ROOT / 'versions').glob('*/rules-paper.tex'))
    families = {}
    sections = {}
    raws = {}
    for p in papers:
        name = p.parent.name
        raw = p.read_text(encoding='utf-8')
        raws[name] = raw
        sections[name] = shared_lines(raw)
        families.setdefault(family_of(p.parent), []).append(name)
    names = sorted(sections)

    # 共识块：所有版本逐字一致。
    if len(names) >= 2:
        lines_by = {n: (ROOT / 'versions' / n / 'rules-paper.tex').read_text(encoding='utf-8').splitlines() for n in names}
        base = names[0]
        for label, start_anchor, end_anchor in CONSENSUS:
            base_block = block_lines(lines_by[base], start_anchor, end_anchor)
            clean = True
            for name in names[1:]:
                block = block_lines(lines_by[name], start_anchor, end_anchor)
                if base_block == block:
                    continue
                ok = False
                clean = False
                diff = next((i for i, (x, y) in enumerate(zip(base_block, block)) if x != y), min(len(base_block), len(block)))
                print(f'FAIL 共识块不一致（{label}）：{base} vs {name}，自第 {diff + 1} 行起不同')
                for who, ls in ((base, base_block), (name, block)):
                    if diff < len(ls):
                        print(f'  {who}: {ls[diff]}')
            if clean:
                print(f'PASS 共识块一致（{label}）：{len(base_block)} 行 × {len(names)} 版')
    else:
        print(f'PASS 共识块一致：当前 {len(names)} 个版本，暂无可比对对象')

    # 同族：整段一致。
    for family, members in sorted(families.items()):
        members = sorted(members)
        if len(members) < 2:
            print(f'PASS 同族整段（{family}）：仅 {members[0]} 一个版本，暂无可比对对象')
            continue
        base = members[0]
        for name in members[1:]:
            a, b = sections[base], sections[name]
            if a == b:
                print(f'PASS 同族整段一致（{family}）：{base} = {name}（{len(a)} 行）')
                continue
            ok = False
            diff = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            print(f'FAIL 同族整段不一致（{family}）：{base} vs {name}，自第 {diff + 1} 行起不同（{len(a)} 行 vs {len(b)} 行）')
            for who, ls in ((base, a), (name, b)):
                if diff < len(ls):
                    print(f'  {who}: {ls[diff]}')

    # 状元等级表：各桌内版本与加赛纸逐字一致（跨件共享内容）。
    final_tex = ROOT / 'champion-final' / 'rules-paper.tex'
    table_sources = {f'版本 {n}': raw for n, raw in raws.items()}
    if final_tex.exists():
        table_sources['加赛纸'] = final_tex.read_text(encoding='utf-8')
    tables = {label: zhuangyuan_table(raw) for label, raw in table_sources.items()}
    t_labels = sorted(tables)
    if len(t_labels) >= 2:
        base = t_labels[0]
        clean = True
        for label in t_labels[1:]:
            if tables[label] == tables[base]:
                continue
            ok = False
            clean = False
            diff = next((i for i, (x, y) in enumerate(zip(tables[base], tables[label])) if x != y),
                        min(len(tables[base]), len(tables[label])))
            print(f'FAIL 状元等级表不一致：{base} vs {label}，自第 {diff + 1} 行起不同')
        if clean:
            print(f'PASS 状元等级表跨件一致：{len(t_labels)} 份源稿（{len(tables[base])} 行）')
    else:
        print('PASS 状元等级表跨件一致：暂无可比对对象')

    # site-data：核心键跨族比对，流程键同族比对。
    datas = {n: json.loads((ROOT / 'versions' / n / 'site-data.json').read_text(encoding='utf-8'))
             for n in names if (ROOT / 'versions' / n / 'site-data.json').exists()}
    if len(datas) >= 2:
        keys = sorted(datas)
        base = keys[0]
        clean = True
        for name in keys[1:]:
            same_family = family_of(ROOT / 'versions' / base) == family_of(ROOT / 'versions' / name)
            for path in JSON_CORE_KEYS + (JSON_FAMILY_KEYS if same_family else []):
                a = normalize_json(path, json_at(datas[base], path))
                b = normalize_json(path, json_at(datas[name], path))
                if a == b:
                    continue
                ok = False
                clean = False
                print(f'FAIL site-data 共享键不一致：{base} vs {name}，键 {".".join(path)}')
        if clean:
            print(f'PASS site-data 共享键一致：{base} 与其余 {len(keys) - 1} 版'
                  f'（核心 {len(JSON_CORE_KEYS)} 组 + 同族流程 {len(JSON_FAMILY_KEYS)} 组）')
    else:
        print(f'PASS site-data 共享键一致：当前 {len(datas)} 份数据，暂无可比对对象')

    # 加赛纸网页数据：状元等级须与各版本网页数据一致。
    final_json = ROOT / 'champion-final' / 'site-data.json'
    if final_json.exists() and datas:
        final_ranks = [(r['name'], tuple(r['faces']), r['rule'], r['compare'])
                       for r in json.loads(final_json.read_text(encoding='utf-8'))['judge']['ranks']]
        clean = True
        for name, data in datas.items():
            version_ranks = [(r['name'], tuple(r['faces']), r['rule'], r['compare'])
                             for r in json_at(data, ('champion', 'ranks'))]
            if version_ranks != final_ranks:
                ok = False
                clean = False
                print(f'FAIL 加赛纸网页数据状元等级不一致：{name}')
        if clean:
            print(f'PASS 加赛纸网页数据状元等级一致：与 {len(datas)} 个版本相同')

    if not ok:
        raise SystemExit('共享内容不一致：改共享规则必须同步对应版本（见 AGENTS.md 四件套）')


if __name__ == '__main__':
    main()
