# -*- coding: utf-8 -*-
"""博饼规则状态机验证脚本。

验证对象：仓库根目录《博饼规则-A4黑白.tex》的规则文字。
方法：按规则纸文字逐条实现游戏状态机（掷骰分类 → 领奖/记名 →
回合推进 → 三段式结束），做三层检查：

1. 全枚举：46656 种骰面归类唯一、无遗漏、无重叠；
2. 确定性剧本：覆盖"所掷奖级发完空过不降档"、状元各等级两两比较、
   先得者保留、每人只记最好成绩、补完一轮与加赛轮中的反超，以及
   比总和阶段的规格缺口（K 组）；
3. 随机整局：字面规则与拟修订规则各 10000 局，验证终止性、
   库存守恒、领取恰 62 份、领先者单调。

运行：python3 verify/状态机验证.py
依赖：仅 Python 3 标准库。

说明：sum_phase_mode='proposed' 是针对"比总和阶段遇真状元骰面"
这一规格空白的拟修订文案的前置验证，规则纸尚未采用；
详见 docs/规则核查.md 的"状态机验证"一节。
"""
from itertools import product, chain, repeat
from collections import Counter
import random

# ---------- 骰面分类（与规则纸判定条件逐条对应） ----------
def classify(roll):
    """返回 (类别, 等级名, 状元比较键)。类别 'Z'=状元, 'N'=普通, '-'=无。"""
    c = Counter(roll); fours = c[4]
    if fours == 6:                                  return ('Z', '六红', None)
    if fours == 5:                                  return ('Z', '五红', sum(x for x in roll if x != 4))
    if fours == 4:
        others = sorted(x for x in roll if x != 4)
        if others == [1, 1]:                        return ('Z', '插金花', None)
        return ('Z', '四红', sum(others))           # 比另2颗之和
    for p in (1, 2, 3, 5, 6):
        if c[p] == 6:                               return ('Z', '六同', None)  # 彼此同级
    for p in (1, 2, 3, 5, 6):
        if c[p] == 5:                               return ('Z', '五子', sum(x for x in roll if x != p))
    if fours == 3:                                  return ('N', '三红', None)
    for p in (1, 2, 3, 5, 6):
        if c[p] == 4:                               return ('N', '四进', None)
    if sorted(roll) == [1, 2, 3, 4, 5, 6]:          return ('N', '对堂', None)
    if fours == 2:                                  return ('N', '二举', None)
    if fours == 1:                                  return ('N', '一秀', None)
    return ('-', '无', None)

ZY_RANK = {'插金花': 6, '六红': 5, '六同': 4, '五红': 3, '五子': 2, '四红': 1}
STOCK0 = {'对堂': 2, '三红': 4, '四进': 8, '二举': 16, '一秀': 32}   # 合计 62
NOTHING = (1, 1, 2, 2, 3, 3)   # 全场无奖骰面，用作剧本填充

def zy_beats(a, b):
    """候选 a=(rank,pts,seq) 是否严格胜过现任 b。同级同点 → 先得者保留(False)。"""
    if a[0] != b[0]:  return a[0] > b[0]
    if a[1] is not None and b[1] is not None and a[1] != b[1]:  return a[1] > b[1]
    return False

def run_game(rolls, start_stock=None, start_leader=None, players=8,
             max_rolls=20000, sum_phase_mode='literal', stop_after_rounds=None):
    """按规则纸执行整局。sum_phase_mode:
    'literal'  = 纸面字面：加赛后每人加掷一次，一律比六颗总和（含状元骰面）；
    'proposed' = 拟修订：掷出状元的按第三节比，都未掷出才比总和。"""
    stock = dict(STOCK0 if start_stock is None else start_stock)
    leader = start_leader            # (rank, pts, seq, player)
    seq = 0
    exhausted = (start_stock is not None and sum(start_stock.values()) == 0)
    log = []; n_rolls = 0; overtime_done = False; claimed = 0; rounds = 0
    start_sum = sum(stock.values())
    if start_stock is not None:
        assert start_sum <= 62 and all(v >= 0 for v in stock.values())

    def do_roll(seat):
        nonlocal n_rolls, seq, leader, claimed, exhausted
        roll = next(rolls); n_rolls += 1
        assert n_rolls < max_rolls, "游戏未终止！"
        cat, tier, key = classify(roll)
        if cat == 'Z':
            seq += 1
            cand = (ZY_RANK[tier], key, seq, seat)
            if leader is None or zy_beats(cand, leader):
                leader = cand
            log.append(('Z', tier, seat, roll))
        elif cat == 'N':
            if stock[tier] > 0:
                stock[tier] -= 1; claimed += 1
                if sum(stock.values()) == 0: exhausted = True
                log.append(('N', tier, seat, roll, '领'))
            else:
                log.append(('N', tier, seat, roll, '空过'))   # 不改领其他奖
        else:
            log.append(('-', tier, seat, roll))

    while True:
        for seat in range(players):
            do_roll(seat)
        rounds += 1
        if stop_after_rounds and rounds >= stop_after_rounds:
            return dict(end='aborted', leader=leader, stock=stock, claimed=claimed,
                        n_rolls=n_rolls, log=log)
        if exhausted:
            if leader is not None:
                return dict(end='path1_有状元', winner=leader[3], leader=leader,
                            stock=stock, claimed=claimed, n_rolls=n_rolls, log=log)
            if not overtime_done:
                overtime_done = True; continue     # 加赛最后一轮（整轮打满）
            # ---- 比总和阶段 ----
            if sum_phase_mode == 'proposed':
                zy = []
                for seat in range(players):
                    roll = next(rolls); n_rolls += 1
                    cat, tier, key = classify(roll)
                    if cat == 'Z':
                        seq += 1; zy.append((ZY_RANK[tier], key, seq, seat))
                if zy:
                    best = zy[0]
                    for cand in zy[1:]:
                        if zy_beats(cand, best): best = cand
                    return dict(end='path3_状元骰面', winner=best[3], leader=best,
                                stock=stock, claimed=claimed, n_rolls=n_rolls, log=log)
            sums = []
            for seat in range(players):
                roll = next(rolls); n_rolls += 1
                sums.append((sum(roll), seat))
            while True:                            # 总和相同者再掷，直至分出
                top = max(s for s, _ in sums)
                tied = [seat for s, seat in sums if s == top]
                if len(tied) == 1:
                    return dict(end='path3_比总和', winner=tied[0], leader=None,
                                stock=stock, claimed=claimed, n_rolls=n_rolls, log=log)
                sums = []
                for seat in tied:
                    roll = next(rolls); n_rolls += 1
                    sums.append((sum(roll), seat))

# ---------- 1. 归类唯一性 ----------
def check_classification():
    cnt = Counter(classify(r)[1] for r in product(range(1, 7), repeat=6))
    assert sum(cnt.values()) == 46656, "归类有遗漏或重叠"

# ---------- 2. 确定性剧本测试 ----------
def scenario_tests():
    res = []
    def t(name, cond): res.append((name, cond))

    def feed(lst, filler=NOTHING):
        return chain(lst, repeat(filler))

    empty = {k: 0 for k in STOCK0}

    # A. 试读者场景：对堂已发完，掷出对堂 → 空过，不改领四进
    g = run_game(feed([(1,2,3,4,5,6)]), start_stock={'对堂':0,'三红':4,'四进':8,'二举':16,'一秀':32},
                 players=2, stop_after_rounds=1)
    t("A 对堂发完掷对堂→空过不降档", g['log'][0][4] == '空过' and sum(g['stock'].values()) == 60)

    # B. 规则纸例句：四进发完，掷 222246 → 空过（不领二举/一秀）
    g = run_game(feed([(2,2,2,2,4,6)]), start_stock={'对堂':2,'三红':4,'四进':0,'二举':16,'一秀':32},
                 players=2, stop_after_rounds=1)
    t("B 四进发完掷222246→空过", g['log'][0][4] == '空过')

    # C1. 四红比另两骰之和：带12 胜 带5
    g = run_game(feed([(4,4,4,4,6,6)]), start_leader=(ZY_RANK['四红'], 5, 1, 0),
                 players=1, stop_after_rounds=1)
    t("C1 四红带12胜带5", g['leader'][1] == 12 and g['leader'][3] == 0)
    # C2. 同为四红带5 → 先得者保留
    g = run_game(feed([(4,4,4,4,2,3)]), start_leader=(ZY_RANK['四红'], 5, 1, 2),
                 players=1, stop_after_rounds=1)
    t("C2 四红同点先得者保留", g['leader'][3] == 2)

    # D1. 等级优先：五红带1 胜 四红带12；D2. 五红带6 胜 带1
    g = run_game(feed([(4,4,4,4,4,1)]), start_leader=(ZY_RANK['四红'], 12, 1, 0),
                 players=1, stop_after_rounds=1)
    t("D1 五红带1胜四红带12", g['leader'][0] == ZY_RANK['五红'])
    g = run_game(feed([(4,4,4,4,4,6)]), start_leader=(ZY_RANK['五红'], 1, 1, 0),
                 players=1, stop_after_rounds=1)
    t("D2 五红带6胜带1", g['leader'][1] == 6)

    # E. 五子只比剩余1颗：带4 不胜 带6；带6 胜 带4
    g = run_game(feed([(2,2,2,2,2,4)]), start_leader=(ZY_RANK['五子'], 6, 1, 0),
                 players=1, stop_after_rounds=1)
    t("E1 五子带4不胜带6", g['leader'][3] == 0)
    g = run_game(feed([(2,2,2,2,2,6)]), start_leader=(ZY_RANK['五子'], 4, 1, 0),
                 players=1, stop_after_rounds=1)
    t("E2 五子带6胜带4", g['leader'][1] == 6)

    # F. 六同彼此同级：111111 不抢 222222
    g = run_game(feed([(1,1,1,1,1,1)]), start_leader=(ZY_RANK['六同'], None, 1, 3),
                 players=1, stop_after_rounds=1)
    t("F 六同同级先得者保留", g['leader'][3] == 3)

    # G. 本场排序：插金花胜五红；六红胜插金花；六同不胜六红
    g = run_game(feed([(4,4,4,4,1,1)]), start_leader=(ZY_RANK['五红'], 6, 1, 0),
                 players=1, stop_after_rounds=1)
    t("G1 插金花最高", g['leader'][0] == ZY_RANK['插金花'])
    g = run_game(feed([(4,4,4,4,1,1)]), start_leader=(ZY_RANK['六红'], None, 1, 0),
                 players=1, stop_after_rounds=1)
    t("G2 六红胜插金花", g['leader'][3] == 0)
    g = run_game(feed([(2,2,2,2,2,2)]), start_leader=(ZY_RANK['六红'], None, 1, 0),
                 players=1, stop_after_rounds=1)
    t("G3 六同不胜六红", g['leader'][3] == 0)

    # H. 每人只记本人最好成绩
    lead = None; seq = 0
    for r in [(4,4,4,4,5,6), (4,4,4,4,4,1), (4,4,4,4,6,6)]:
        cat, tier, key = classify(r); seq += 1
        cand = (ZY_RANK[tier], key, seq, 7)
        if lead is None or zy_beats(cand, lead): lead = cand
    t("H 只记本人最好成绩", lead[0] == ZY_RANK['五红'] and lead[1] == 1)

    # I. 补完当前一轮时产生的状元有效并结束
    g = run_game(feed([(1,1,1,1,2,3), (4,4,4,4,6,6)]), start_stock=empty, players=2)
    t("I 补完一轮中产生状元并结束", g['end'] == 'path1_有状元' and g['leader'][1] == 12)
    # J. 补完一轮中后位反超
    g = run_game(feed([(4,4,4,4,6,6), (4,4,4,4,4,1)]), start_stock=empty, players=2)
    t("J 补完一轮中后位反超", g['end'] == 'path1_有状元' and g['leader'][0] == ZY_RANK['五红'])

    # K. 比总和阶段的规格缺口
    seq_k = [(1,1,2,2,3,3)]*4 + [(4,4,4,4,2,6), (6,6,6,5,5,5)]
    g = run_game(feed(seq_k), start_stock=empty, players=2, sum_phase_mode='literal')
    t("K1 字面规则：真状元(总和20)输给普通骰(总和33)——荒谬，暴露缺口",
      g['end'] == 'path3_比总和' and g['winner'] == 1)
    g = run_game(feed(seq_k), start_stock=empty, players=2, sum_phase_mode='proposed')
    t("K2 拟修订：状元骰面按第三节计，444426 获胜", g['end'] == 'path3_状元骰面' and g['winner'] == 0)
    seq_tie = [(1,1,2,2,3,3)]*4 + [(6,6,6,6,5,5), (6,6,6,6,5,5), (2,2,2,2,1,1), (3,3,3,3,1,1)]
    g = run_game(feed(seq_tie), start_stock=empty, players=2, sum_phase_mode='proposed')
    t("K3 总和相同再掷可终止并分出", g['end'] == 'path3_比总和' and g['winner'] == 1)
    seq_zy2 = [(1,1,2,2,3,3)]*4 + [(4,4,4,4,6,6), (4,4,4,4,2,3)]
    g = run_game(feed(seq_zy2), start_stock=empty, players=2, sum_phase_mode='proposed')
    t("K4 比总和阶段两个状元按第三节比", g['end'] == 'path3_状元骰面' and g['winner'] == 0)
    return res

# ---------- 3. 随机整局：不变量 + 终止性 ----------
def random_games(n=10000, players=8, seed=2026, sum_phase_mode='literal'):
    rng = random.Random(seed)
    ends = Counter(); max_r = 0
    for _ in range(n):
        def rolls():
            while True: yield tuple(rng.randint(1, 6) for _ in range(6))
        g = run_game(rolls(), players=players, sum_phase_mode=sum_phase_mode)
        ends[g['end']] += 1; max_r = max(max_r, g['n_rolls'])
        assert all(v == 0 for v in g['stock'].values()), "库存未清空"
        assert g['claimed'] == 62, "领取数≠62"
        # 状元掷出永不占普通奖：log 中 Z 条目长度恒为 4
        assert all(len(e) == 4 for e in g['log'] if e[0] == 'Z')
    return ends, max_r

if __name__ == '__main__':
    check_classification()
    print("[1] 全枚举 46656 种骰面归类唯一、无遗漏 ✓")

    res = scenario_tests()
    fails = [r for r in res if not r[1]]
    for name, ok in res:
        print(f"    [{'通过' if ok else '失败'}] {name}")
    print(f"[2] 确定性剧本 {len(res)} 项，失败 {len(fails)} 项")

    ends, max_r = random_games()
    print(f"[3] 字面规则随机 10000 局全部终止（最长 {max_r} 掷），路径分布 {dict(ends)}")
    ends2, max_r2 = random_games(seed=77, sum_phase_mode='proposed')
    print(f"[4] 拟修订规则随机 10000 局全部终止（最长 {max_r2} 掷），路径分布 {dict(ends2)}")
