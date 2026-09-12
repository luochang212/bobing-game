# AGENTS.md

本仓库交付一张中秋活动用的 A4 黑白单页博饼规则纸。核心资产是 LaTeX 源稿，
PDF 由源稿编译生成，Python 脚本对规则文字做机器验证，docs 记录每个决策的依据。
规则内容定位是"本次活动统一版"（本场约定），不得表述为各地统一传统。

## 文件职责

- `博饼规则-A4黑白.tex`：规则纸唯一源稿，规则语义以它为准。
- `output/pdf/博饼规则-A4黑白.pdf`：编译产物，只由 `make pdf` 生成，不要手改。
- `verify/状态机验证.py`：按规则纸文字逐条实现的状态机与验证（46656 种骰面
  全枚举归类、20 项确定性剧本、随机整局模拟）。它镜像 tex 的规则，改规则必须同步改。
- `verify/网页阅读验证.py`：讲解页的浏览器回归检查（七种视口 × Chromium/WebKit、
  目录跳转、无脚本阅读），依赖 Playwright，运行方式见 `docs/移动端阅读核查.md`。
- `verify/规则纸输出验证.py`：检查 PDF 单页与底部安全线，渲染三档清晰度并解码
  二维码，可更新 `docs/preview.png`；依赖与命令见 README。
- `docs/规则核查.md`：决策与证据的留痕——资料来源、每处修订的原因、已知规格空白。
  改规则必须同步补记。
- `docs/移动端阅读核查.md`：网页阅读体验的核查记录——两轮修订的判断依据与
  可重复检查命令。
- `README.md`：使用说明 + 游戏流程 mermaid 图（与脚本实现一一对应）。
- `site/`：讲解版网页（Astro + Tailwind，部署到 GitHub Pages，workflow 为
  `.github/workflows/site.yml`）。定位是"解释与举例"，不是第二份规则权威源：
  页面措辞逐句对齐 tex，页头注明"以现场纸质规则为准"；改规则若影响页面
  举例，同步更新。
- `build/`：编译中间产物。

## 常用命令

```sh
make pdf                        # 编译（latexmk + XeLaTeX），产物复制到 output/pdf/
python3 verify/状态机验证.py     # 状态机验证，必须全部通过
mdls -name kMDItemNumberOfPages output/pdf/博饼规则-A4黑白.pdf   # 页数，必须 = 1
pdftotext -bbox output/pdf/博饼规则-A4黑白.pdf - \
  | grep -oE 'yMax="[0-9.]+"' | sort -t'"' -k2 -n | tail -1
# yMax 为内容最低点；页高 841.89pt，下边距 1.25cm≈35.5pt，必须 ≤ 806
```

编译依赖本机 MacTeX 与 macOS 字体（Songti SC / Hiragino Sans GB）；右上角二维码由
MacTeX 自带的 `qrcode` 宏包直接生成，目标为 `https://www.luochang.ink/bobing-game/`。
找不到 tex 命令先 `export PATH="/Library/TeX/texbin:$PATH"`。
换字体或宏包会使非 macOS 环境无法编译，需慎重。

讲解页（site/）：`cd site && npm install && npm run dev` 本地开发，
`npm run build` 产物在 `site/dist/`；部署由 Actions 自动完成（仅 `site/**`
变化时触发），规则纸 PDF 由 CI 在部署时复制为 `rules-paper.pdf`。

## 改规则的"三件套"同步

tex、verify 脚本、docs 描述同一套规则，任何语义修改一次改齐：

1. 改 `博饼规则-A4黑白.tex`；
2. 同步修改 `verify/状态机验证.py` 的 classify / 状态机（受影响的剧本一并改）；
3. 在 `docs/规则核查.md` 增补修订记录（改了什么、依据是什么）；
4. `make pdf` 重编译；README 的流程图若受影响同步更新。

## 硬性约束

- **PDF 输出位置协议**：仓库唯一交付 PDF 是 `output/pdf/博饼规则-A4黑白.pdf`；编译一律走
  `make pdf`（latexmk 中间产物只落 `build/`）。禁止在仓库根目录直接运行 xelatex——根目录
  或 `output/` 之外出现同名 PDF 即散落产物，直接删除，不入库、不 review。
- **单页**：任何改动后 PDF 页数必须仍为 1。当前内容底部约 798pt，安全线
  806pt，余量仅约 8pt——新增整行文字必然溢出，先想清楚删什么或压哪里。
- **黑白**：只用灰阶与黑底白字（黑底"4"表示红四，是黑白印刷对红色的替代），
  不得引入彩色。
- **排版方向**：版面按"留白转化为行距与字号"优化过，不要为填空间编造
  栏目、字段或文字。
- **表述纪律**：不使用有歧义的措辞（例："最高奖级已发完"曾被迫改为
  "所掷奖级发完"）；新增规则句要能通过"试读者会怎么误读"这一问。

## 验证标准

提交前完整跑一遍：

1. `python3 verify/状态机验证.py` 全绿（归类唯一、20 剧本、两组各 10000 局）；
2. PDF 仍 1 页，yMax ≤ 806，`pdftotext` 抽查确认新措辞已写入；
3. 若改了流程图，节点/边与脚本状态机逐条对照；
4. 若改了 `site/`，跑 `verify/网页阅读验证.py`（Chromium 与 WebKit，命令见
   `docs/移动端阅读核查.md`）。
5. 若改了规则纸排版或二维码，跑 `verify/规则纸输出验证.py` 并更新 README 预览；
   纯排版修改可用 `--compare-ref` 对照修改前提交，确认规则正文未变。

第 1、2 项由 GitHub Actions（`.github/workflows/verify.yml`）在每次 push/PR 时自动
兜底执行：ubuntu 上跑状态机验证，并用 poppler 检查已提交 PDF 的单页与 yMax 红线。
PDF 编译因字体依赖不在 CI 内，仍以本机 `make pdf` 为准。

## 当前已知状态

- 比总和阶段遇真状元骰面的规格空白已收口：结束条款现为"有人掷出状元，就按第三节比较；
  都未掷出，就比六颗点数总和"，已写入 tex；脚本 `sum_phase_mode='proposed'` 对应
  现行条款，`'literal'` 保留为修订前对照。
- "总和相同者再掷，直至分出"为概率 1 终止（非对抗性终止），对活动现场
  可接受；脚本与 docs 均已如实标注，不要在文档里写成"必然结束"。
- 提交信息用中文一句话摘要 + 要点列表，参考 `git log` 既有风格。
