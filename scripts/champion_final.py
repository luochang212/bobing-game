# -*- coding: utf-8 -*-
"""状元王加赛状态机验证脚本。

验证对象：champion-final/rules-paper.tex 的加赛规则。桌内判定分类
（classify / zy_beats）共用 scripts/state_machine.py，其全枚举归类在该
脚本的 CI 步骤中已覆盖，本脚本不重复。

模型：players 名桌状元围一桌轮流掷骰——
  - 每掷当场与全场最好成绩比较：严格更优（等级→带点）则取代为领先，
    挑战窗口重置为"其他每人各掷一次"；等级与带点相同，先掷出者保留；
  - 挑战窗口耗尽（领先确立后其他每人各掷一次——含未超越的状元掷——而无人
    超越）→ 封盘，领先者当选；
  - 兜底：连续 dry_rounds 轮无任何状元 → 每人加掷一次（一掷两用）：
    有状元按比较分出名次；都未掷出比六颗点数总和，同和者再掷直至分出。

运行：python3 scripts/champion_final.py
依赖：仅 Python 3 标准库。
"""
from itertools import chain, repeat
from collections import Counter
import random

from state_machine import classify, zy_beats, ZY_RANK, NOTHING


def run_final(rolls, players=14, max_rolls=5000, dry_rounds=10):
    leader = None            # (rank, pts, seq, player)
    seq = 0
    window = None            # 距封盘还差的挑战掷数；None=尚无领先
    dry = 0
    n_rolls = 0
    log = []

    def do_roll(seat):
        """掷一次。返回 'sealed'（当场封盘）、'z'（掷出状元）或 None。"""
        nonlocal leader, seq, window, n_rolls
        roll = next(rolls); n_rolls += 1
        assert n_rolls < max_rolls, "游戏未终止！"
        cat, tier, key = classify(roll)
        took_lead = False
        if cat == 'Z':
            seq += 1
            cand = (ZY_RANK[tier], key, seq, seat)
            took_lead = leader is None or zy_beats(cand, leader)
            if took_lead:
                leader = cand
                window = players - 1      # 新领先需被其他每人各挑战一次
        log.append(('Z' if cat == 'Z' else '-', tier, seat, roll))
        if took_lead:
            return 'z'
        # 未超越的状元同样是"其他每位各掷一次"中的一掷，照常消耗挑战窗口；
        # 领先者本人的掷骰（seat == leader[3]，含更差状元）不消耗。
        if leader is not None and seat != leader[3]:
            window -= 1
            if window == 0:
                return 'sealed'
        return 'z' if cat == 'Z' else None

    while True:
        z_count = 0
        for seat in range(players):
            result = do_roll(seat)
            if result == 'sealed':
                return dict(end='sealed', winner=leader[3], leader=leader,
                            n_rolls=n_rolls, log=log)
            if result == 'z':
                z_count += 1
        dry = 0 if z_count else dry + 1
        if dry >= dry_rounds:
            # 兜底：每人加掷一次（一掷两用）
            sums = []; zy = []
            for seat in range(players):
                roll = next(rolls); n_rolls += 1
                cat, tier, key = classify(roll)
                if cat == 'Z':
                    seq += 1; zy.append((ZY_RANK[tier], key, seq, seat))
                sums.append((sum(roll), seat))
            if zy:
                best = zy[0]
                for cand in zy[1:]:
                    if zy_beats(cand, best): best = cand
                return dict(end='shootout_zhuangyuan', winner=best[3], leader=best,
                            n_rolls=n_rolls, log=log)
            while True:                   # 总和相同者再掷，直至分出
                top = max(s for s, _ in sums)
                tied = [seat for s, seat in sums if s == top]
                if len(tied) == 1:
                    return dict(end='shootout_sum', winner=tied[0], leader=None,
                                n_rolls=n_rolls, log=log)
                sums = []
                for seat in tied:
                    roll = next(rolls); n_rolls += 1
                    sums.append((sum(roll), seat))


# ---------- 确定性剧本 ----------
def scenario_tests():
    res = []
    def t(name, cond): res.append((name, cond))
    def feed(lst, filler=NOTHING):
        return chain(lst, repeat(filler))

    # M1. 封盘：领先确立后其他每人各掷一次无人超越 → 领先者当选
    g = run_final(feed([(4,4,4,4,6,6)]), players=3)
    t("M1 领先站住一轮挑战即封盘", g['end'] == 'sealed' and g['winner'] == 0
      and g['n_rolls'] == 3)

    # M2. 反超重置：五红取代四红，挑战窗口重新起算
    g = run_final(feed([(4,4,4,4,2,3), (4,4,4,4,4,1)]), players=3)
    t("M2 更高级别反超并重置挑战", g['end'] == 'sealed' and g['winner'] == 1
      and g['leader'][0] == ZY_RANK['五红'])

    # M3. 同级同点：先掷出者保留，挑战掷数照常消耗
    g = run_final(feed([(4,4,4,4,2,3), (4,4,4,4,2,3)]), players=3)
    t("M3 同级同点先得者保留", g['end'] == 'sealed' and g['winner'] == 0
      and g['n_rolls'] == 3)

    # M4. 领先者自我刷新：更好的状元重置挑战窗口
    g = run_final(feed([(4,4,4,4,2,3), NOTHING, (4,4,4,4,6,6)]), players=3)
    t("M4 领先者自我刷新重置挑战", g['end'] == 'sealed' and g['winner'] == 2
      and g['leader'][1] == 12 and g['n_rolls'] == 5)

    # M5. 兜底比总和：连续 dry 轮无状元 → 每人加掷一次，总和大者当选
    g = run_final(feed([NOTHING, NOTHING, (6,6,6,6,5,5), (2,2,2,2,1,1)]),
                  players=2, dry_rounds=1)
    t("M5 无状元兜底比总和", g['end'] == 'shootout_sum' and g['winner'] == 0
      and g['n_rolls'] == 4)

    # M6. 兜底一掷两用：加掷中出现状元按比较分出，不比总和
    g = run_final(feed([NOTHING, NOTHING, (4,4,4,4,6,6), (2,2,2,2,1,1)]),
                  players=2, dry_rounds=1)
    t("M6 兜底加掷一掷两用", g['end'] == 'shootout_zhuangyuan' and g['winner'] == 0)

    # M7. 兜底同和再掷：33 平 33 → 再掷分出
    g = run_final(feed([NOTHING, NOTHING, (6,6,6,6,5,5), (6,6,6,6,5,5),
                        (4,4,4,4,1,1), (2,2,2,2,1,1)]), players=2, dry_rounds=1)
    t("M7 同和再掷直至分出", g['end'] == 'shootout_sum' and g['winner'] == 0
      and g['n_rolls'] == 6)

    # M8. 未超越的状元照常消耗挑战窗口（纸面"其他每位各掷一次"）：
    # 1 号四红带5（状元、未超越）计入其挑战掷 → 3 掷封盘而非 5 掷
    g = run_final(feed([(4,4,4,4,6,6), (4,4,4,4,2,3)]), players=3)
    t("M8 未超越的状元消耗窗口", g['end'] == 'sealed' and g['winner'] == 0
      and g['n_rolls'] == 3)
    return res


# ---------- 随机整局：终止性 + 胜者合法性 ----------
def random_games(n=10000, players=14, seed=2026, dry_rounds=10):
    rng = random.Random(seed)
    ends = Counter(); total = 0; max_r = 0
    for _ in range(n):
        def rolls():
            while True: yield tuple(rng.randint(1, 6) for _ in range(6))
        g = run_final(rolls(), players=players, dry_rounds=dry_rounds)
        ends[g['end']] += 1; total += g['n_rolls']; max_r = max(max_r, g['n_rolls'])
        if g['end'] == 'sealed':
            assert g['winner'] == g['leader'][3], "封盘胜者必须是领先者本人"
        elif g['end'] == 'shootout_zhuangyuan':
            assert g['winner'] == g['leader'][3], "加掷状元胜者必须与领先记录一致"
    return ends, max_r, total / n


if __name__ == '__main__':
    res = scenario_tests()
    fails = [r for r in res if not r[1]]
    for name, ok in res:
        print(f"    [{'通过' if ok else '失败'}] {name}")
    print(f"[1] 加赛确定性剧本 {len(res)} 项，失败 {len(fails)} 项")

    ends, max_r, avg = random_games()
    print(f"[2] 加赛随机 10000 局（14 人桌，兜底 10 轮）全部终止："
          f"平均 {avg:.0f} 掷，最长 {max_r} 掷，路径分布 {dict(ends)}")
