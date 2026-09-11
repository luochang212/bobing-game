.PHONY: pdf

pdf:
	latexmk -xelatex -halt-on-error -interaction=nonstopmode '博饼规则-A4黑白.tex'
	mkdir -p output/pdf
	cp 'build/博饼规则-A4黑白.pdf' 'output/pdf/博饼规则-A4黑白.pdf'
