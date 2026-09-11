# 中秋博饼规则

一份用于中秋活动现场的 A4 黑白单页规则纸，包含道具准备、玩法步骤、奖级表、状元大小和桌号填写区。

## 文件

- `博饼规则-A4黑白.tex`：可编辑的 LaTeX 源稿。
- `output/pdf/博饼规则-A4黑白.pdf`：可直接打印的 PDF。
- `.latexmkrc`：默认使用 XeLaTeX，编译中间文件集中在 `build/`。
- `Makefile`：编译并复制最终 PDF。
- `build/`：编译产物；`build/previous/` 保存整理前的失败编译记录。

## 本机生成

使用本机已安装的 MacTeX / TeX Live、`latexmk`、`make`，以及 macOS 的 `Songti SC` 和 `Hiragino Sans GB` 字体，不需要联网下载资源。

```sh
make pdf
```

请使用 XeLaTeX 编译；pdfLaTeX 不支持源稿使用的系统字体设置。如果终端找不到 TeX 命令，可先执行 `export PATH="/Library/TeX/texbin:$PATH"`。

打印时选择 A4 纵向、实际大小（100%）和黑白打印。

## 内容说明

保留原稿的玩法和状元等级约定，仅修正奖级表标题的排序方向。各地博饼规则可能不同，活动开始前请按规则纸的提示确认本桌约定。
