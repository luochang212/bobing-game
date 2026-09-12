.PHONY: pdf

pdf:
	latexmk -xelatex -halt-on-error -interaction=nonstopmode 'rules-paper.tex'
	mkdir -p output/pdf
	cp 'build/rules-paper.pdf' 'output/pdf/rules-paper.pdf'
