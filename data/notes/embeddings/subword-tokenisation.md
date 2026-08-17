# Subword tokenisation

Why a model's idea of a token is not the same as splitting on spaces, which matters for us
because our chunk sizes are counted in whitespace tokens.

Word-level vocabularies cannot cope with words they have never seen, and every misspelling
and identifier becomes an unknown token. Character-level models have no unknowns but their
sequences are long and each symbol carries almost no meaning. Subword methods sit between:
common words stay whole, rare words break into pieces.

BPE starts from characters and repeatedly merges the most frequent adjacent pair until the
vocabulary reaches the target size. WordPiece, which BERT and therefore MiniLM use, merges
on likelihood gain instead of raw frequency, and marks continuation pieces with `##`.
Unigram LM, used by SentencePiece, goes the other way: start with a large candidate set
and prune the pieces whose removal costs least likelihood.

Practical consequences I keep bumping into.

Technical prose expands. "tokenisation" might be `token ##isation`, a snake_case
identifier can become five or six pieces, and a hex string explodes. So a chunk of 512
whitespace tokens is comfortably over 600 word pieces of technical writing, which is well
past MiniLM's 256 limit. The tail gets truncated in silence.

British spellings sometimes split differently from American ones, because the training
corpus was mostly American. "normalisation" and "normalization" are not the same token
sequence. Probably a non-issue for retrieval since both map into similar regions, but it
is a real difference and someone will ask about it in the viva.

Numbers are poorly handled almost everywhere. Do not expect an embedding to know that 2019
is close to 2020.

For the report: I should measure the whitespace-to-wordpiece ratio on our own corpus
rather than quoting the usual 1.3 figure from a blog post. One line with the tokeniser and
a mean over the chunks would do it.
