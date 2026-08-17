# Demo corpus

These 33 markdown files are a demo corpus, written for this project so that the tool and
the evaluation run out of the box without anyone having to supply their own notes. They
are not real personal notes: the ethics condition for the submission was that nothing
personal enters the repository, so this corpus was written for the purpose.

They are meant to look like genuine study notes for the module, which is why the
formatting is inconsistent. Some files have YAML front matter with tags and some do not,
some are split into sections and some are one block, and there are TODOs and code snippets
left in place. That variation is deliberate; a loader that only copes with tidy input is
not much use on a real vault.

A few pairs of notes cover related ideas in deliberately different vocabulary, for example
`retrieval/ann-search.md` and `retrieval/fuzzy-vector-lookup.md`, or
`embeddings/cosine-vs-dot-product.md` and `embeddings/measuring-closeness.md`. Those pairs
are where semantic search should find something that keyword search cannot. A few other
notes contain rare exact tokens, such as an environment variable name or an error string,
where BM25 should win instead.

`README.md` files are skipped by the loader, so this file is not indexed.

To use your own notes instead, point `NOTES_DIR` at the folder:

    NOTES_DIR=~/Documents/vault python -m noterecall index
    NOTES_DIR=~/Documents/vault python -m noterecall search "your query"

and re-run `make eval` to regenerate the numbers. Note that `evaluation/goldset.yaml` was
written against this corpus and its relevance judgements are meaningless for any other
one, so the evaluation will fail validation until you write your own gold set.
