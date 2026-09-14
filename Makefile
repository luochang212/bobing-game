# 双指针：current 指向桌内版本（versions/<名>/），scope 指向活动场景（single/multi）。
# 交付集合随 scope：multi ＝ 桌内纸＋加赛纸（两份 PDF、两个网页）；single ＝ 仅桌内纸。
CURRENT := $(shell cat current)
SCOPE := $(shell cat scope)
VERSION_DIR := versions/$(CURRENT)

ifneq ($(SCOPE),single)
ifneq ($(SCOPE),multi)
$(error scope 文件内容须为 single 或 multi，当前为 '$(SCOPE)')
endif
endif

.PHONY: pdf pdf-all pdf-final list-versions

# 按双指针同步交付位：桌内纸永远编译；加赛纸仅 multi 场景交付，single 时清掉残留。
pdf:
	@test -f '$(VERSION_DIR)/rules-paper.tex' || { echo "失败：current 指向 '$(CURRENT)'，但 $(VERSION_DIR)/rules-paper.tex 不存在"; exit 1; }
	latexmk -xelatex -halt-on-error -interaction=nonstopmode -outdir='build/$(CURRENT)' '$(VERSION_DIR)/rules-paper.tex'
	mkdir -p output/pdf
	cp 'build/$(CURRENT)/rules-paper.pdf' 'output/pdf/rules-paper.pdf'
ifeq ($(SCOPE),multi)
	@$(MAKE) --no-print-directory pdf-final
else
	@rm -f output/pdf/champion-final.pdf
	@echo "单桌场景：交付仅桌内纸，已确保无加赛纸残留（output/pdf/champion-final.pdf）"
endif

# 状元王加赛纸：编译并落位交付；仅多桌场景的交付集合包含它（make pdf 会连带调用）。
pdf-final:
ifeq ($(SCOPE),single)
	@echo "失败：当前 scope=single（单桌），加赛纸不属于交付集合；编译检查请用 make pdf-all"; exit 1
endif
	latexmk -xelatex -halt-on-error -interaction=nonstopmode -outdir='build/champion-final' 'champion-final/rules-paper.tex'
	mkdir -p output/pdf
	cp 'build/champion-final/rules-paper.pdf' 'output/pdf/champion-final.pdf'

# 编译全部版本与加赛纸供检查（中间产物只落 build/<名>/，不动交付位）。
pdf-all:
	@for v in $$($(MAKE) --no-print-directory list-versions); do \
		echo "== 编译版本 $$v =="; \
		latexmk -xelatex -halt-on-error -interaction=nonstopmode -outdir='build/'$$v 'versions/'$$v'/rules-paper.tex' || exit 1; \
	done
	@echo "== 编译加赛纸（仅落 build/） =="
	latexmk -xelatex -halt-on-error -interaction=nonstopmode -outdir='build/champion-final' 'champion-final/rules-paper.tex'

.PHONY: list-versions
list-versions:
	@ls versions/
