# LaTeX and reference management

Overleaf for the report because three people editing one file in Word ends badly. Free
tier allows one collaborator; the university licence covers the rest and takes a day to
come through, so request it early.

Zotero for references, with the Better BibTeX plugin exporting `references.bib` on save
into the Overleaf project via the Git bridge. Citation keys in author-year-shortword form,
so `karpukhin2020dpr`, set once in the Better BibTeX key format so they never change.
Keys that change break every `\cite` silently.

Harvard style for this module. `natbib` with the `agsm` style gives the right output.
`\citep` for parenthetical, `\citet` when the author is the subject of the sentence. Half
the corrections on last term's coursework were `\citet` where it should have been
`\citep`.

Errors I hit and their causes:

Undefined citation warnings that persist after adding the reference: run pdflatex, bibtex,
then pdflatex twice more. Overleaf usually handles it, but it caches, and the fix is to
clear the cached files from the logs menu.

`! LaTeX Error: File 'algorithm2e.sty' not found` on my local TeX Live but fine on
Overleaf, because I installed the small scheme. `tlmgr install algorithm2e`.

Figures: export matplotlib to PDF, not PNG. Vector text stays crisp when the marker zooms
in and the file is usually smaller. `plt.savefig("fig.pdf", bbox_inches="tight")`. Set the
figure size in inches to the final column width and do not scale it in LaTeX, or the font
sizes come out inconsistent between figures.

Word count in Overleaf counts LaTeX commands unless you use the built-in counter, which
uses TeXcount and gets it roughly right. Check against the brief's limit with some margin,
because the two never agree exactly.
