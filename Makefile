# 版本指针：current 文件一行版本名，指向 versions/ 下的子目录。
CURRENT := $(shell cat current)
VERSION_DIR := versions/$(CURRENT)

.PHONY: pdf pdf-all

# 只编译当前版本，并落位为唯一交付 PDF。
pdf:
	@test -f '$(VERSION_DIR)/rules-paper.tex' || { echo "失败：current 指向 '$(CURRENT)'，但 $(VERSION_DIR)/rules-paper.tex 不存在"; exit 1; }
	latexmk -xelatex -halt-on-error -interaction=nonstopmode -outdir='build/$(CURRENT)' '$(VERSION_DIR)/rules-paper.tex'
	mkdir -p output/pdf
	cp 'build/$(CURRENT)/rules-paper.pdf' 'output/pdf/rules-paper.pdf'

# 编译全部版本供检查（中间产物各归 build/<版本>/），不改写交付位。
pdf-all:
	@for v in $$($(MAKE) --no-print-directory list-versions); do \
		echo "== 编译版本 $$v =="; \
		latexmk -xelatex -halt-on-error -interaction=nonstopmode -outdir='build/'$$v 'versions/'$$v'/rules-paper.tex' || exit 1; \
	done

.PHONY: list-versions
list-versions:
	@ls versions/
