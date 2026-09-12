# 本地开发与机器验证

直接使用规则纸可下载现成 PDF，无需准备开发环境。本文面向需要修改规则纸排版或讲解网页、运行验证脚本的贡献者。

## 本地开发

| 用途 | 技术与依赖 |
| --- | --- |
| 规则纸排版 | LaTeX、MacTeX（latexmk + XeLaTeX）、macOS 字体 |
| 讲解网页 | Astro、Tailwind CSS、Node.js 与 npm |
| 规则验证 | Python 3，仅依赖标准库 |
| PDF 预览与二维码核查 | Poppler、Python 3 + Pillow / ZXing-C++ |
| 网页回归检查 | Python 3 + Playwright（Chromium / WebKit） |
| 自动检查与部署 | GitHub Actions、Poppler、GitHub Pages |

### 编译规则纸

在仓库根目录运行：

```sh
make pdf
```

`make pdf` 编译仓库根 `current` 指针指向的版本（版本表见 README），中间产物按版本落在 `build/<版本>/`，最终 PDF 始终输出到 [`output/pdf/rules-paper.pdf`](../output/pdf/rules-paper.pdf)。切换版本 = 改 `current` 后重新 `make pdf` 并提交。状元王加赛纸独立于版本，`make pdf-final` 单独编译，产物为 [`output/pdf/champion-final.pdf`](../output/pdf/champion-final.pdf)。把 `versions/` 下全部版本与加赛纸各编译一遍供检查（不改写交付位）：

```sh
make pdf-all
```

依赖 macOS 字体 **Songti SC / Hiragino Sans GB**。

<details>
<summary>找不到 TeX 命令？</summary>

安装 MacTeX 后，将工具目录加入当前终端的 PATH，再编译：

```sh
export PATH="/Library/TeX/texbin:$PATH"
make pdf
```

本稿使用 XeLaTeX，pdfLaTeX 不支持当前字体设置。请统一通过 `make pdf` 编译。

</details>

### 生成预览与核查二维码

二维码地址直接写在 TeX 的 `\qrcode` 命令中，由 MacTeX 自带宏包生成矢量图。改地址后运行 `make pdf`（加赛纸为 `make pdf-final`），再用[输出验证脚本](../scripts/paper_output_check.py)检查并更新预览；加赛纸需追加 `--pdf output/pdf/champion-final.pdf`，且其二维码指向 `/bobing-game/champion-final/`，核查时传入 `--url https://www.luochang.ink/bobing-game/champion-final/`。

首次准备核查环境：

```sh
brew install poppler
python3 -m venv tmp/pdf-tools
tmp/pdf-tools/bin/pip install pillow zxing-cpp
```

每次编译后运行：

```sh
tmp/pdf-tools/bin/python scripts/paper_output_check.py --preview-output docs/preview.png
```

脚本检查单页与 806pt 底部安全线，在 `tmp/pdf-review/` 生成提取文字及 100、150、300 DPI 图片，并逐张解码二维码，核对目标地址。全部通过后才更新 README 预览。纯排版修改时可附加 `--compare-ref <提交号>`，对照该版本的规则正文；更换网址时同时传入 `--url <新地址>`。核查依赖不参与 PDF 编译。

### 启动讲解网页

```sh
cd site
npm install
npm run dev
```

打开终端显示的本地地址，访问 `/bobing-game/` 路径。构建与预览：

```sh
npm run build
npm run preview
```

产物位于 `site/dist/`。[部署工作流](../.github/workflows/site.yml) 配置为在 `main` 分支的 `site/**`、`versions/**`、`champion-final/**` 或工作流文件变化时部署到 GitHub Pages，也支持手动触发，线上地址为 [www.luochang.ink/bobing-game](https://www.luochang.ink/bobing-game/)。主页按 `current` 指针渲染桌内版本，`/champion-final/` 为状元王加赛页（不随指针）。部署时会将两份规则纸复制为 `rules-paper.pdf` 与 `champion-final.pdf`；本地预览构建产物时，如需使用页面上的 PDF 下载入口，可先在 `site/` 目录执行：

```sh
cp ../output/pdf/rules-paper.pdf dist/rules-paper.pdf
cp ../output/pdf/champion-final.pdf dist/champion-final.pdf
```

## 机器验证

在仓库根目录运行：

```sh
python3 scripts/state_machine.py
python3 scripts/champion_final.py
python3 scripts/version_consistency.py
```

脚本另以 ruff 做静态检查（`pip install ruff` 后运行 `ruff check scripts/`，配置见 `.ruff.toml`，CI 同步执行）。

| 检查层级 | 覆盖内容 |
| --- | --- |
| 全枚举 | 46656 种骰面归类 |
| 确定性剧本 | 20 项（tiered）＋5 项（pooled），覆盖奖品发完、状元比较、先得者保留、补轮反超与结束边界 |
| 随机整局 | 修订前对照与现行结束条款各 10000 局，检查终止情况、库存守恒与路径分布 |
| 状元王加赛 | 7 项剧本＋10000 局随机，覆盖领先挑战与封盘、无状元兜底、加掷一掷两用、同和再掷 |
| 版本共享段 | 各源稿共享段与 site-data 共享键两两比对，改共享规则必须同步对应源稿 |

<details>
<summary>查看验证输出节选</summary>

```text
[1] 全枚举 46656 种骰面归类唯一、无遗漏 ✓
[2] 确定性剧本 20 项，失败 0 项
[3] 字面规则随机 10000 局全部终止
[4] 拟修订规则随机 10000 局全部终止
```

脚本保留历史命名：`sum_phase_mode='proposed'` 对应规则纸现行结束条款，`literal` 为修订前对照。随机模拟全部结束是观测结果；普通奖阶段和总和同分重掷为概率 1 终止，不保证固定掷骰次数内结束。

</details>

[验证工作流](../.github/workflows/verify.yml) 在推送到 `main` 和提交 PR 时运行状态机检查，并用 Poppler 检查已提交 PDF 的单页与版面红线。PDF 编译依赖本机字体，仍需在本机完成。

手机阅读体验另有[核查记录与浏览器回归检查](mobile-reading-check.md)，覆盖首屏玩法、规则字号、目录跳转与无脚本阅读。
