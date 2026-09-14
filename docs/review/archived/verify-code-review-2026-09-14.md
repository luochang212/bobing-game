# 对《Code Review 与内容 Review 报告（2026-09-14）》的核实报告

- **核实对象**：`docs/review/code-review-2026-09-14.md`（审查对象为 `main @ fbfe654`）
- **核实日期**：2026-09-14
- **核实时仓库状态**：`main @ fbfe654`，工作区仅 `docs/review/` 未跟踪，无源稿改动
- **核实方法**：逐条静态对照（引文、行号、断言逻辑）＋ 破坏性实验（C1 复现、C2 对调等级）＋
  本机实跑三个验证脚本复核基线
- **核实纪律**：论断先转命题再验证；"属实"与"值得修"分开判定；复现命令见附录，可整段粘贴重跑

## 结论一览

| 编号 | 报告论断 | 判定 | 核实方式 |
| --- | --- | --- | --- |
| C1 | 加赛状态机：未超越的状元掷不消耗挑战窗口 | **坐实**（实验复现，且演示了胜者被改变） | 复现 A/B，见下 |
| C2 | G2/G3 断言恒真、G2 名字与规则相反 | **坐实**（破坏实验全绿） | 对调 ZY_RANK 实测，见下 |
| I1 | champion-final.astro 注释过时 + `current` 死变量 | 坐实 | 静态核对 |
| I2 | `pdf-all` "不改写交付位"声明不实 | 坐实 | Makefile 逐行核对 |
| I3 | tex ↔ site-data 文字绑定缺失 | 坐实（观察类） | 通读 version_consistency.py |
| I4 | 加掷/比总和代码块重复 | 坐实；"保留并登记"的处置合理 | 对照两段代码 |
| N1 | `lines_by` 重读文件 | 坐实 | 静态核对 |
| N2 | 两个 workflow action 版本不统一 | 坐实 | grep uses |
| N3 | pooled 无 `start_pool >= 0` 断言 | 坐实 | 静态核对 |
| 内容 | flexible 页脚烧入"多桌"配置的定位张力 | 坐实 | 四处证据，见"指针模型"节 |
| 验证状态 | 审查时三脚本全绿；yMax/ruff 未本地跑 | 属实 | 本次实跑三脚本亦全绿 |

**总评：报告零虚构、零夸大；两处 Critical 定级恰当。C1 的影响在报告里是推断性表述
（"可以改变胜者"），本次实测把它坐实为已演示的事实。**

---

## C1：未超越的状元掷不消耗挑战窗口 —— 坐实（Critical 定级恰当）

**命题化**：3 人桌，0 号四红带 12 领先后，1 号掷出四红带 5（状元、未超越）、2 号无奖。
纸面读法：其余二人已各掷一次且无人超越，第 3 掷封盘、0 号当选。脚本是否如此？

**纸面**（引文属实）：`champion-final/rules-paper.tex:78`

> 当选：领先成绩产生后，从其下一位起，**其他每位参赛者各掷一次**而无人超越时，
> 领先者当选状元王，加赛结束。

掷出未超越的状元也是"各掷一次"中的一掷，应消耗挑战窗口。

**代码**（属实）：`scripts/champion_final.py:40-47` 的 `cat == 'Z'` 分支提前 `return 'z'`，
窗口递减只存在于非状元分支（49-52 行）。挑战者掷出未超越的状元时，这一掷不计入
"各掷一次"。

**复现 A（报告原文场景）**：实测输出 `{'end': 'sealed', 'winner': 0, 'n_rolls': 5}`，
纸面读法应为 3 掷——与报告完全一致。

**复现 B（胜者被改变，本次新增）**：让 1 号在第 2 轮掷出五红带 1——纸面上加赛早在
第 3 掷就以 0 号当选结束，这一掷不该存在；脚本却让 1 号反超获胜：

```
feed = [444466, 444423, NOTHING, NOTHING, 444441, NOTHING]  # 按 r1s0,r1s1,r1s2,r2s0,r2s1,r2s2 座次
实测：{'end': 'sealed', 'winner': 1, 'n_rolls': 7}
纸面：end=sealed, winner=0, n_rolls=3（第 2 轮根本不该发生）
```

复现陷阱备注：构造胜者改变场景时，反超那一掷必须排到挑战者本人手里（第 2 轮的
1 号位）。第一次排错座次（五红落到 0 号手里）只会得到 winner=0，误以为影响仅是拖长。

**旁证（均属实）**：M3 剧本名写着"挑战掷数照常消耗"（`champion_final.py:110`），但
断言（111 行）未钉 `n_rolls`，该性质从未被测到；脚本 docstring 与 AGENTS.md 均与纸面
一致，唯独代码不一致——正是仓库核心契约"脚本镜像纸面"的违约。

**修法确认**：报告建议（Z 分支未取代领先时走与非状元掷相同的窗口递减与封盘判断）
已推演：`seat != leader[3]` 守卫天然覆盖"领先者本人掷出更差/同级同点状元"不消耗
窗口的情形，方案成立。修复时应新增钉住 `n_rolls` 的剧本（复现 A/B 即现成素材）。

**值得修**：是。能改变胜者的规则镜像偏差，属本仓库最严重的一类缺陷。

## C2：G2/G3 断言恒真、G2 名字与规则相反 —— 坐实

**命题化**：把 `ZY_RANK` 中插金花与六红的等级对调（直接违背纸面"插金花……本场最高"），
tiered 剧本是否会红？

**破坏实验**：对调后实测 20 项 tiered 剧本**依然全部通过**——整个测试套件没有任何
一项钉住这个排序。

**恒真断言静态论证**：G2/G3（`scripts/state_machine.py:212-217`）都是 `players=1` 且
`start_leader` 就是 0 号本人；无论骰面是否取代现任，`g['leader'][3]` 都是 0，
断言 `g['leader'][3] == 0` 恒真。

**名字矛盾（属实）**：两版 tex（`versions/flexible/rules-paper.tex:90`、
`versions/classic/rules-paper.tex:89`）与 `ZY_RANK`（`state_machine.py:53`）均为
插金花最高；G2 名字"六红胜插金花"与 G 组注释（208 行）直接矛盾，G1 名字
"插金花最高"与 G2 互斥，符合"改了 G1 忘了 G2"的猜测。

**值得修**：是。插金花压过六红恰是本稿最反常识、最依赖"本场约定"辩护的一处排序，
偏偏是唯一没被钉住的地方；修复成本极低（换座位 + 改名）。

## Improvements 与 Nitpicks 逐条

- **I1 坐实**：`site/src/pages/champion-final.astro:12-13` 注释"两个页面互不引用"已被
  `71c1a4b` 推翻——58 行页脚 `cross` 链回主页，主页也经 `footer.cross` 链来（当前
  `current=flexible`）；15 行 `current` 读入后从未使用。
- **I2 坐实**：`Makefile:20-26` 注释"不改写交付位"，但 `pdf-all` 调用 `pdf-final`，
  后者 `cp` 到 `output/pdf/champion-final.pdf`（15-18 行）；AGENTS.md"常用命令"一节
  同样声明不实。实际无害（重编相同内容），属声明与行为不符。
- **I3 坐实（观察类）**：`scripts/version_consistency.py` 只做 tex↔tex（共识块/同族/
  状元表跨件）与 json↔json（site-data 两档、加赛页数据）比对，确无 tex↔json 的
  文字绑定；`web_reading_check.py` 只把骰面绑到 tex。缺口存在，弱检查是否值得加
  属独立决策。
- **I4 坐实**：`state_machine.py:128-151` 与 `champion_final.py:67-89` 近乎逐字重复。
  报告"保留重复、出现第三处再抽取"的处置与镜像哲学一致，登记不动。
- **N1 坐实**：`version_consistency.py:104` 的 `lines_by` 重读了 96-97 行已存入
  `raws` 的文件。
- **N2 坐实**：`site.yml:24-25` 用 checkout@v7 / setup-node@v7，`verify.yml:12,14` 用
  checkout@v4 / setup-python@v5。
- **N3 坐实**：`state_machine.py:74-85` 仅 tiered 模型有库存非负断言，pooled 的
  `start_pool` 无对应检查。

## 验证状态声明的复核

三脚本本次实跑全绿（全枚举、tiered 20 + pooled 5 剧本、加赛 7 剧本、随机整局、
共享内容六项 PASS），与报告"审查时实跑全绿"一致。yMax 与 ruff 报告如实标注未本地
复核（CI 兜底），本次亦未重复。

## 勘误与修正记录

- **无证伪项**：报告全部论断核实为真。
- **一处升级**：C1 的影响在报告中的表述是"可以改变胜者"（推断），本次以复现 B
  将其坐实为已演示的事实（脚本判 1 号胜、纸面判 0 号胜）。
- **一处复现细节补充**：胜者改变场景的喂骰必须按座次排到反超者本人手中，排错
  座次只会观察到"拖长"而误判影响面（详见 C1 复现陷阱备注）。

---

## 附：版本指针模型问题（与报告"内容 Review"的页脚张力同源）

**一句话**：指针只表达了"奖品模型"一个轴，"单桌还是多桌"这个同样真实的活动配置
没有归属，渗进四个地方各自为政。报告的内容审查（flexible 自称"单桌多桌通用"却
硬编码 `footer.cross`）与用户独立发现的"加赛成品不随指针变化"是同一个建模缺口的
两个切面——两个互不知情的视角指向同一处，说明不是错觉。

**现状证据**：

1. `versions/flexible/rules-paper.tex:4` 自称"单桌多桌通用，无全场环节"，但其
   `site-data.json:11-12` 硬编码 `footer.cross` 链向加赛页；classic 放祝福语。
   自称双场景通用的版本，网站页脚只会按其中一种场景渲染。
2. 加赛纸的成品无条件存在：`output/pdf/champion-final.pdf`、`/champion-final/` 网页
   （`champion-final.astro` 不随指针）、CI 无条件校验（`verify.yml:35,72-74`）、
   部署时无条件复制（`site.yml:37`）。切到 classic 办单桌活动，加赛物料仍在线上、
   仍被交付与验证——按本仓库"指针与产物一致、散落产物即删"自己的标准不自洽。
3. `web_reading_check.py:94,98` 按页脚有无加赛入口分支——同一比特的第四处编码。
4. 反向缺口：模型表达不了"多桌 + classic（指定奖品数量）"的组合。
5. 发炎史：`71c1a4b`"页脚按版本场景驱动"就是在页脚层面打的补丁，未触及建模。

**两轴模型**：真实配置空间是 {奖品模型：指定数量 classic ／ 若干 flexible} ×
{桌数：单桌 ／ 多桌}。用户列的三态（单桌-指定、单桌-若干、多桌-若干）是该空间的
投影，缺"多桌-指定"——可能永远用不上，但应是有意识的取舍而非疏漏。

**交付集合派生表**（用户预期，核实成立）：

| 场景 | 交付 PDF | 网页 | 页脚 |
| --- | --- | --- | --- |
| 单桌-指定（classic） | 1 份（rules-paper.pdf） | 1 个（/） | 祝福语 |
| 单桌-若干（flexible） | 1 份 | 1 个 | 祝福语 |
| 多桌-若干（flexible） | 2 份（+champion-final.pdf） | 2 个（+/champion-final/） | 互跳 |

**实现形态两选**：

1. *平铺场景目录*（原案）：`versions/` 下"单桌-若干"与"多桌-若干"是两个完整自含
   目录，仅页脚键与定位 README 不同。符合"版本即自含目录"的现有哲学；代价是为
   一个页脚键差异整份复制 flexible 的 tex 与 site-data，规则改动多一处同步面。
2. *双轴配置*（推荐）：`versions/` 保持奖品模型轴不动，桌数做成第二个配置位
   （如 `current` 旁加 `scope` 文件）。页脚键从 site-data 删除、由 scope 派生；
   `make pdf` 在多桌时连带编译加赛纸；站点按 scope 决定是否产出 `/champion-final/`；
   CI 在单桌模式**断言加赛产物不存在**（防"改了指针忘清产物"，与特征句兜底同构）。

推荐第 2 种，理由：单桌/多桌的差异**不触及任何纸面内容**（桌内纸一字不变，变的
只是交付集合与页脚），为这点差异复制整份版本目录会让"两个 flexible"看起来内容
有别而实际没有；双轴还免费覆盖"多桌-指定"组合。加赛纸内容本身与奖品模型无关、
单一共享源是现状中**正确**的部分，任何形态都应保留。

**代价面（形态 2）**：Makefile、`site.yml`（条件复制）、`verify.yml`（条件校验＋缺失
断言）、`index.astro` 页脚派生（`site-data` 删 footer 键）、`web_reading_check.py`
（分支改挂 scope）、AGENTS.md 版本模型章节与 docs 三篇相应改写。中等、偏机械。

**是否需要重构**：指针模型是架构形状问题（一个隐式比特散落四处编码），需要的是
一次有界的重构，不是局部修补；C1/C2 则是局部缺陷，十行以内修复，不需要重构。

**建议顺序**（不混提交）：

1. 修 C1、C2——规则正确性优先，按四件套在 `docs/rule-audit.md` 补记；C1 的修复在
   任何指针形态下都原样存活，先做不浪费。
2. 定指针形态（平铺 vs 双轴）并重构构建/CI/站点。
3. I1、I2 顺手处理；I3 可在重构时一并考虑（页脚键移出后检查面缩小）。

---

## 附录：复现命令

以下整段粘贴可重跑（仓库根目录）。复现 A/B 依赖 `scripts/` 内模块，C2 实验直接
改内存中的 `ZY_RANK`，不落盘。

```sh
# 基线：三脚本应全绿
python3 scripts/state_machine.py && python3 scripts/champion_final.py \
  && python3 scripts/version_consistency.py

# C1 复现 A＋B（报告场景 + 胜者改变）
cd scripts && python3 - <<'EOF'
import sys; sys.path.insert(0, '.')
from itertools import chain, repeat
from state_machine import NOTHING
import champion_final as cf

g = cf.run_final(chain([(4,4,4,4,6,6), (4,4,4,4,2,3)], repeat(NOTHING)), players=3)
print("A:", {k: g[k] for k in ('end','winner','n_rolls')}, "纸面应为 n_rolls=3")

feed = [(4,4,4,4,6,6), (4,4,4,4,2,3), NOTHING, NOTHING, (4,4,4,4,4,1), NOTHING]
g2 = cf.run_final(chain(feed, repeat(NOTHING)), players=3)
print("B:", {k: g2[k] for k in ('end','winner','n_rolls')}, "纸面应为 winner=0, n_rolls=3")
EOF

# C2 破坏实验：对调插金花/六红等级，剧本应仍全绿（证明无区分力）
cd scripts && python3 - <<'EOF'
import state_machine as sm
sm.ZY_RANK['插金花'], sm.ZY_RANK['六红'] = sm.ZY_RANK['六红'], sm.ZY_RANK['插金花']
fails = [n for n, ok in sm.scenario_tests() if not ok]
print("对调后失败项：", fails if fails else "无——全部通过，断言无区分力坐实")
EOF
```
