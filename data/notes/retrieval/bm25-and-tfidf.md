# BM25 and why it is still hard to beat

TF-IDF weights a term by how often it appears in the document and how rare it is across
the collection. BM25 is the same instinct with two corrections that turn out to matter a
lot.

First, term frequency saturates. A document containing a word twenty times is not twenty
times more about that word than one containing it once. BM25 pushes tf through
tf / (tf + k1), so extra occurrences give diminishing returns. k1 around 1.2 to 1.5.

Second, length normalisation is partial and tunable. Long documents naturally contain
more of everything, so raw counts favour them. The b parameter interpolates between no
normalisation at all (b = 0) and full normalisation by document length over average
document length (b = 1). Default b = 0.75.

The IDF part is log((N - df + 0.5) / (df + 0.5) + 1). The +1 inside the log is there to
stop the score going negative for terms that appear in more than half the collection.

Why it survives: it needs no training, no GPU, no embedding model, it is exactly
interpretable, and it is unbeatable when the user types a token that appears verbatim in
exactly one document. Identifiers, error messages, surnames, module codes. A dense
embedding smears all of those into a general neighbourhood of "technical looking text".

Where it fails is the obvious complement. Zero lexical overlap means zero score. If a note
says "cut the text into overlapping windows" and the query says "chunking strategy", BM25
returns nothing useful and the embedding model handles it without effort.

`rank_bm25` is a small pure-Python implementation. BM25Okapi takes a list of token lists
at construction and `get_scores(query_tokens)` returns a score per document. Fine at this
corpus size; it recomputes over the whole collection per query, so it would not scale, but
that is not what we are measuring.

Stopwords: I drop a short hand-written list. Removing them barely changes ranking because
IDF already flattens them, but it keeps the token lists smaller.
