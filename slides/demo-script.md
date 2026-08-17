# Live demo run sheet

Presenter: Mounika Maddula. Slide 15 is the holding slide; stay on it while the terminal is
shared. Budget four minutes. Everything below was run on the demo laptop on 10 August 2026
and the output is what actually came back.

No API key and no network are needed. The index backend is `local` and the MiniLM weights
are already in `~/.cache/huggingface`, so `HF_HUB_OFFLINE=1` is set to prove the point
rather than to work around anything. If Wi-Fi at the venue is down, nothing here changes.

## Before you present

- `cd` into the repository and activate the venv, so the prompt shows `(.venv)`.
- Run the whole sequence once, then clear the terminal. A cold first run pays a couple of
  seconds to load the model and it looks like a hang.
- Terminal at about 120 columns and a large font. The result snippets are wide.
- `python -m noterecall stats` should already report 33 notes.

## Setup, before you start talking

    cd ~/Desktop/project/project-1-noterecall
    source .venv/bin/activate
    export INDEX_BACKEND=local
    export HF_HUB_OFFLINE=1
    clear

`sentence-transformers` prints a one-line `Loading weights: 100%|...| 103/103` progress bar
to stderr on the first model load of each command. It is not an error and it is not shown
in the expected output below.

## 1. What is in the corpus

    python -m noterecall stats

Say: thirty-three markdown notes, and the same notes chunked three ways. Note the bottom
row: at 512 tokens we get 33 chunks from 33 notes, which is the caveat Vinay flagged.

    Notes in ~/project-1-noterecall/data/notes: 33
      chunk128: 98 chunks if indexed
      chunk256: 65 chunks if indexed
      chunk512: 33 chunks if indexed

      backend: local
      directory: ~/project-1-noterecall/.index
      total_vector_count: 196
        chunk128: vector_count=98, dimension=384, size_mb=0.144
        chunk256: vector_count=65, dimension=384, size_mb=0.095
        chunk512: vector_count=33, dimension=384, size_mb=0.048

## 2. Rebuild the index we are about to search

    python -m noterecall index --chunk-size 512 --rebuild

Say: this is the whole indexing pipeline, live. Load, chunk, embed, upsert. On this corpus
it is a tenth of a second, and it would be the same code against Pinecone with a key set.

    Loaded 33 notes from ~/project-1-noterecall/data/notes
    Embedding with sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) into the local index
    chunk512: 33 chunks, embedded in 0.1s, stored in 0.0s

    Index stats
      backend: local
      directory: ~/project-1-noterecall/.index
      total_vector_count: 196
        chunk128: vector_count=98, dimension=384, size_mb=0.144
        chunk256: vector_count=65, dimension=384, size_mb=0.095
        chunk512: vector_count=33, dimension=384, size_mb=0.048

## 3. A paraphrase query, semantic (gold query q06)

    python -m noterecall search "cutting a long document into pieces before indexing it" --chunk-size 512 --top-k 3

Say: the note that answers this is called "Chunking strategies" and it never uses the word
"cutting" or the word "pieces". Semantic search puts it first anyway.

Each result prints a snippet line under it, omitted here for width. Everything else is
verbatim.

    semantic search over chunk512, top 3

     1   0.540  Chunking strategies  (retrieval/chunking-strategies.md)
     2   0.418  Supervisor meeting, 11 February  (module/supervisor-meeting-11-feb.md)
     3   0.407  How I actually write these notes  (misc/writing-workflow.md)

## 4. The same query, keyword

    python -m noterecall search "cutting a long document into pieces before indexing it" --mode keyword --chunk-size 512 --top-k 3

Say: same corpus, same chunks, only the scoring changes. BM25 does not return the right
note at all. The top hit is there because it happens to contain the word "cutting", in a
sentence about cutting generation out of the design. This is one of the paraphrase queries
behind the 0.875 against 0.700 MRR gap.

    keyword search over chunk512, top 3

     1   5.298  Supervisor meeting, 11 February  (module/supervisor-meeting-11-feb.md)
     2   5.209  Subword tokenisation  (embeddings/subword-tokenisation.md)
     3   5.017  How do you say two pieces of text are alike  (embeddings/measuring-closeness.md)

## 5. An exact-token query, semantic (gold query q15)

    python -m noterecall search karpukhin2020dpr --chunk-size 512 --top-k 3

Say: now the other direction. This is a bibtex key, and it is written out in the reading
list note. Semantic gets it at rank two, behind an unrelated note, and the scores are all
low because a citation key means nothing to the embedding model.

    semantic search over chunk512, top 3

     1   0.160  Presentation plan  (module/presentation-plan.md)
     2   0.139  Reading list for the literature review  (module/reading-list.md)
     3   0.094  Subword tokenisation  (embeddings/subword-tokenisation.md)

## 6. The same query, keyword

    python -m noterecall search karpukhin2020dpr --mode keyword --chunk-size 512 --top-k 3

Say: BM25 puts it first, and the second hit is the other note that mentions the key. It
returns two results rather than three because only two chunks score above zero, which is
the honest answer. This is why keyword scores a perfect 1.000 MRR on exact tokens.

    keyword search over chunk512, top 2

     1   2.605  Reading list for the literature review  (module/reading-list.md)
     2   2.567  LaTeX and reference management  (misc/latex-and-references.md)

## 7. Hybrid on the same query, if there is time

    python -m noterecall search karpukhin2020dpr --mode hybrid --chunk-size 512 --top-k 3

Say: reciprocal rank fusion over both rankings. The right note comes back to rank one
without us tuning a weight, which is why our recommendation is to ship hybrid rather than
pick a side.

    hybrid search over chunk512, top 3

     1   0.033  Reading list for the literature review  (module/reading-list.md)
     2   0.016  Presentation plan  (module/presentation-plan.md)
     3   0.016  LaTeX and reference management  (misc/latex-and-references.md)

Then hand back for slide 16.

## Fallback: the model cannot be loaded

If `~/.cache/huggingface` is empty on the machine we end up presenting from and there is no
network, the sentence-transformers path cannot run. Switch to the hashing embedder, in a
separate index directory so the real index is not overwritten:

    export EMBEDDING_BACKEND=hashing
    export LOCAL_INDEX_DIR=.index-hashing
    python -m noterecall index --chunk-size 512 --rebuild
    python -m noterecall search "cutting a long document into pieces before indexing it" --chunk-size 512 --top-k 3

    Loaded 33 notes from ~/project-1-noterecall/data/notes
    Embedding with hashing (384 dimensions) into the local index
    chunk512: 33 chunks, embedded in 0.0s, stored in 0.0s
    ...
    semantic search over chunk512, top 3

     1   0.194  Combining two rankings without tuning weights  (retrieval/hybrid-fusion.md)
     2   0.193  BM25 and why it is still hard to beat  (retrieval/bm25-and-tfidf.md)
     3   0.170  How I actually write these notes  (misc/writing-workflow.md)

Say this out loud if you have to use it: this is a hashed bag of words with no model behind
it. It proves the pipeline runs end to end, and you can see it does not find the chunking
note, because it has no semantics at all. It is a smoke test and none of our reported
numbers come from it. Then go straight to the figures on slides 10 to 12 and talk to those
instead.

Afterwards, `rm -rf .index-hashing` and unset both variables.

## If the terminal fails completely

Slides 10, 11 and 12 already carry the three figures, and `results/summary.md` has every
number in the deck. Talk to slide 11 and move on. Do not spend presentation time debugging.
