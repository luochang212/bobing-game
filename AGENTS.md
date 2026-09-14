# AGENTS.md

本仓库交付一套中秋活动用的 A4 黑白单页博饼规则物料，支持多版本：**桌内规则纸**
（按奖品模型分版本）与**状元王加赛纸**（独立一张，服务决赛桌）。PDF 由源稿编译
生成，Python 脚本对规则文字做机器验证，docs 记录每个决策的依据。规则内容定位是
"本次活动统一版"（本场约定），不得表述为各地统一传统。

## 版本模型

- 仓库根的 `current` 是指针文件，内容一行版本名；`make pdf` 只编译它指向的版本，
  `output/pdf/rules-paper.pdf` 是唯一桌内交付 PDF，永远等于当前版本。网站构建时读
  同一指针，只渲染当前版本（见 `site/`）。
- `versions/<名>/` 每个版本自含全部版本特有内容：
  - `rules-paper.tex`：完整独立原稿（不做宏模板、不 `\input` 共享文件）；
  - `README.md`：定位、依据链接，以及行首声明的元数据——**规则族**（同族
    版本整段比对，跨族只锁定共识块，奖品模型不同即跨族）、**特征句**（可
    多行，交付 PDF 必须全部包含）与**排除句**（可选，交付 PDF 不得包含）。
    特征句与排除句共同保证 CI 的"指针与产物一致"检查在各版本之间无歧义
    （改了 `current` 忘重编译、或放错版本产物即红）；
  - `site-data.json`：讲解页全量文案（Astro 构建时按指针加载）。
- `versions/` 下的版本都是**桌内规则纸**：只写桌内玩法，不出现状元王内容
  （状元王是决赛桌的另一个游戏，由独立的加赛纸承载，见下）。
- `champion-final/` 是**状元王加赛纸**，独立一张、不随指针变化：各桌状元同台
  轮掷决胜的完整规则（参加座次、判定与当选、连续无状元时、小提醒）。其状元
  等级表与各桌版本第三节逐字一致，由 `scripts/version_consistency.py` 跨件比对；
  停止条件已成文（挑战一轮站住封盘＋10 轮无状元比总和兜底），设计依据见
  `docs/rule-audit.md`。纸上措辞平铺直叙，不用"异常/兜底/封盘"一类行话。
- 各版本必须一致的共享内容由 `scripts/version_consistency.py` 兜底：同族
  整段（奖级表、状元表、异常与收尾、记录栏）、跨族共识块（第一、三节与
  出碗叠骰行）、状元等级表跨件比对、site-data 核心/流程键两档；改共享内容
  必须同步对应源稿。
- 换版本 = 改 `current` → `make pdf` → 提交。新增版本 = 新建 `versions/<名>/`
  （tex、README 含特征句、site-data.json）→ `make pdf-all` 编译检查 → 全套验证。
- 版本名只描述自己（如 `classic`＝标准 63 份），"当前用哪个"只由
  `current` 表达；文件名一律英文，文件内容保持中文。

## 文件职责

- `current`：版本指针，一行版本名。
- `versions/`：版本仓库（结构见上）。
- `scripts/state_machine.py`：按桌内规则纸文字逐条实现的状态机与验证（46656 种骰面
  全枚举归类、tiered 20 项＋pooled 5 项确定性剧本、随机整局模拟）。它镜像 tex
  的规则（`prize_model='tiered'|'pooled'` 两种奖品模型），改规则必须同步改。
- `scripts/champion_final.py`：状元王加赛状态机与验证（领先挑战窗口与封盘、
  无状元兜底、加掷一掷两用、同和再掷；确定性剧本＋随机整局）。镜像加赛纸规则，
  改加赛规则必须同步改。
- `scripts/version_consistency.py`：各源稿共享内容一致性检查（纯标准库，CI 兜底），
  按规则族分档比对，状元等级表跨件比对。
- `scripts/web_reading_check.py`：讲解页的浏览器回归检查（七种视口 × Chromium/WebKit、
  目录跳转、无脚本阅读），以当前版本 tex 为骰面基准；依赖 Playwright，运行方式见
  `docs/mobile-reading-check.md`。
- `scripts/paper_output_check.py`：检查交付 PDF 单页与底部安全线，渲染三档清晰度并
  解码二维码，可更新 `docs/preview.png`；`--compare-ref` 可对照历史提交（含英文化前
  旧路径回退）；依赖与命令见 `docs/local-dev-and-verification.md`。
- `champion-final/`：状元王加赛纸（源稿 `rules-paper.tex`＋README 含特征句），
  编译产物为 `output/pdf/champion-final.pdf`。
- `docs/rule-audit.md`：决策与证据的留痕——资料来源、每处修订的原因、已知规格空白。
  改规则必须同步补记。
- `docs/mobile-reading-check.md`：网页阅读体验的核查记录与可重复检查命令。
- `docs/local-dev-and-verification.md`：编译、预览与二维码核查、网页开发与机器验证
  的运行手册；README 简述各环节并链接过去。
- `README.md`：使用说明 + 版本表（仓库内的版本列表）+ 游戏流程 mermaid 图。
- `site/`：讲解网页（Astro + Tailwind，部署到 GitHub Pages，workflow 为
  `.github/workflows/site.yml`）。主页构建时读 `current`、加载当前版本的
  `site-data.json` 渲染桌内规则，不设多版本路由；页脚按版本数据二选一——
  多桌有状元王环节的版本放互跳入口（`footer.cross`），纯桌内版本放祝福语
  占位（`footer.blessing`）；`/champion-final/` 为加赛纸
  的网页版，数据取自 `champion-final/site-data.json`，不随指针。主页正文不出现
  加赛内容（与桌纸不含状元王同构）。定位是"解释与举例"，
  不是第二份规则权威源：页面措辞逐句对齐 tex，页头注明"以现场纸质规则为准"；
  改规则若影响页面举例，同步更新对应源稿的 site-data.json。
- `build/`：编译中间产物，按版本分目录。

## 常用命令

```sh
make pdf                        # 编译 current 指向的版本，产物复制到 output/pdf/rules-paper.pdf
make pdf-final                  # 编译状元王加赛纸，产物复制到 output/pdf/champion-final.pdf
make pdf-all                    # 编译全部版本与加赛纸供检查（只落 build/，不动交付位）
python3 scripts/state_machine.py          # 桌内状态机验证，必须全部通过
python3 scripts/champion_final.py         # 加赛状态机验证，必须全部通过
python3 scripts/version_consistency.py    # 共享内容一致，必须全部通过
mdls -name kMDItemNumberOfPages output/pdf/rules-paper.pdf      # 页数，必须 = 1
pdftotext -bbox output/pdf/rules-paper.pdf - \
  | grep -oE 'yMax="[0-9.]+"' | sort -t'"' -k2 -n | tail -1
# yMax 为内容最低点；页高 841.89pt，下边距 1.25cm≈35.5pt，必须 ≤ 806（两份 PDF 都要满足）
```

编译依赖本机 MacTeX 与 macOS 字体（Songti SC / Hiragino Sans GB）；右上角二维码由
MacTeX 自带的 `qrcode` 宏包直接生成，目标为 `https://www.luochang.ink/bobing-game/`。
找不到 tex 命令先 `export PATH="/Library/TeX/texbin:$PATH"`。
换字体或宏包会使非 macOS 环境无法编译，需慎重。

讲解页（site/）：`cd site && npm install && npm run dev` 本地开发，
`npm run build` 产物在 `site/dist/`；部署由 Actions 自动完成（`site/**`、
`versions/**` 或 `current` 变化时触发），规则纸 PDF 由 CI 在部署时复制为
`rules-paper.pdf`。

## 改规则的"四件套"同步

tex、验证脚本、docs 描述同一套规则，任何语义修改一次改齐：

1. 改受影响版本的 `versions/<名>/rules-paper.tex`；改加赛规则则改
   `champion-final/rules-paper.tex`；共享段改动必须同步**所有共享它的源稿**；
2. 同步修改 `scripts/state_machine.py` 的 classify / 状态机（受影响的剧本一并改）；
3. 在 `docs/rule-audit.md` 增补修订记录（改了什么、依据是什么）；
4. `make pdf` 重编译；README 的流程图与受影响版本的 site-data.json 一并更新。

## 硬性约束

- **PDF 输出位置协议**：仓库交付两份 PDF——桌内纸 `output/pdf/rules-paper.pdf`
  （内容必须等于 `current` 指向的版本，CI 用特征句兜底）与加赛纸
  `output/pdf/champion-final.pdf`（内容必须与 `champion-final/` 源稿一致）；
  编译一律走 `make pdf` / `make pdf-final`（latexmk 中间产物只落 `build/<名>/`）。
  禁止在仓库根目录直接运行 xelatex——根目录或 `output/` 之外出现同名 PDF 即
  散落产物，直接删除，不入库、不 review。
- **单页**：任何版本改动后其 PDF 页数必须仍为 1。当前内容底部约 798pt，安全线
  806pt，余量仅约 8pt——新增整行文字必然溢出，先想清楚删什么或压哪里。
- **黑白**：只用灰阶与黑底白字（黑底"4"表示红四，是黑白印刷对红色的替代），
  不得引入彩色。
- **排版方向**：版面按"留白转化为行距与字号"优化过，不要为填空间编造
  栏目、字段或文字。
- **表述纪律**：不使用有歧义的措辞（例："最高奖级已发完"曾被迫改为
  "所掷奖级发完"）；新增规则句要能通过"试读者会怎么误读"这一问。

## 验证标准

提交前完整跑一遍：

1. `ruff check scripts/` 全绿（需 `pip install ruff`；配置见 `.ruff.toml`，CI 同步执行）；
2. `python3 scripts/state_machine.py` 全绿（归类唯一、tiered 20 剧本＋pooled 5 剧本、三组随机）；
3. `python3 scripts/champion_final.py` 全绿（加赛 8 剧本、随机整局）；
4. `python3 scripts/version_consistency.py` 全绿（同族整段、跨族共识块、状元等级表跨件、site-data 两档）；
5. 两份交付 PDF 均 1 页、yMax ≤ 806；桌内 PDF 含当前版本 README 声明的特征句，
   加赛纸 PDF 含其 README 声明的特征句；`pdftotext` 抽查确认新措辞已写入；
6. 若改了流程图，节点/边与脚本状态机逐条对照；
7. 若改了 `site/`，跑 `scripts/web_reading_check.py`（Chromium 与 WebKit，命令见
   `docs/mobile-reading-check.md`）。
8. 若改了规则纸排版或二维码，跑 `scripts/paper_output_check.py` 并更新 README 预览；
   纯排版修改可用 `--compare-ref` 对照修改前提交，确认规则正文未变。

第 1—5 项由 GitHub Actions（`.github/workflows/verify.yml`）在每次 push/PR 时自动
兜底执行：ubuntu 上跑两个状态机与共享内容检查，并用 poppler 检查两份已提交 PDF 的
单页、yMax 红线与特征句。PDF 编译因字体依赖不在 CI 内，仍以本机 `make pdf`
（改共享段时用 `make pdf-all` 把所有源稿都编一遍）为准。

## 当前已知状态

- 版本模型 2026-09-12 上线，同日按"每张纸只服务自己那张桌子"完成剥离：桌内纸
  回归纯桌内规则（`classic` 标准六十三份 / `flexible` 灵活奖品两版），状元王加赛
  独立成纸 `champion-final/`（原带钩子的两版已删，git 历史可查）。
- 状元王加赛停止条件已成文：领先成绩被其他每人各挑战一次而无人超越即封盘；
  连续 10 轮无状元则每人加掷、一掷两用、比总和兜底。该规则与加赛纸、状态机
  三方互为镜像；收敛依据与对赛事先例的偏离见 `docs/rule-audit.md`。
- 比总和阶段遇真状元骰面的规格空白已收口：结束条款现为"有人掷出状元，就按第三节比较；
  都未掷出，就比六颗点数总和"，已写入 tex；脚本 `sum_phase_mode='proposed'` 对应
  现行条款，`'literal'` 保留为修订前对照。
- "总和相同者再掷，直至分出"为概率 1 终止（非对抗性终止），对活动现场
  可接受；脚本与 docs 均已如实标注，不要在文档里写成"必然结束"。
- 提交信息用中文一句话摘要 + 要点列表，参考 `git log` 既有风格。
