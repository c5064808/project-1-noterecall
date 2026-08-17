# Sampling and the biases that follow

Selection bias: the sample is drawn in a way that relates to the thing being measured.
The survey of how people feel about the library, conducted in the library. Everything
downstream is contaminated and no amount of sample size fixes it, because more data just
means a more precise estimate of the wrong quantity.

Survivorship bias is the special case that keeps catching people out. Wald's aircraft
armour story is the standard example: you only see the planes that came back, so the
undamaged areas on those planes are the areas where damage is fatal.

Non-response bias: those who answer differ from those who do not, and usually differ on
exactly the dimension you care about. Response rates below about 30 percent make any
population claim shaky.

## Applied to this project

This is the part that belongs in the limitations section.

The gold set is thirty queries I wrote after reading my own notes. I know what is in the
corpus, so I unconsciously wrote queries that are answerable. Real users search for things
that are not there, and the tool's behaviour when the answer is absent is completely
untested by this design.

The corpus itself is my notes on retrieval and statistics, which is a narrow and unusually
technical vocabulary with a lot of shared jargon between documents. Retrieval on it is
probably harder than on a general vault, because the documents are all close together in
embedding space. Or possibly easier, because the queries can use precise words. I cannot
tell which without a second corpus, so the honest claim is that the result is about this
corpus.

Judgements are binary and made by one person with no second annotator, so there is no
inter-annotator agreement to report. Named as a limitation, not solved.

The fix for all of these is out of scope for the module: a second corpus, a second
annotator, and queries collected from someone who has not read the notes.
