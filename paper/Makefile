MAIN    = main
OUTDIR  = build
LATEX   = pdflatex
PATH   := $(HOME)/.TinyTeX/bin/x86_64-linux:$(PATH)
export PATH

.PHONY: pdf clean

pdf:
	@mkdir -p $(OUTDIR)
	$(LATEX) -output-directory=$(OUTDIR) -interaction=nonstopmode -synctex=1 $(MAIN).tex
	bibtex $(OUTDIR)/$(MAIN)
	$(LATEX) -output-directory=$(OUTDIR) -interaction=nonstopmode -synctex=1 $(MAIN).tex
	$(LATEX) -output-directory=$(OUTDIR) -interaction=nonstopmode -synctex=1 $(MAIN).tex
	@echo "✓  $(OUTDIR)/$(MAIN).pdf"

clean:
	rm -f $(OUTDIR)/*.aux $(OUTDIR)/*.log $(OUTDIR)/*.toc \
	      $(OUTDIR)/*.bbl $(OUTDIR)/*.blg $(OUTDIR)/*.out \
	      $(OUTDIR)/*.fls $(OUTDIR)/*.fdb_latexmk
