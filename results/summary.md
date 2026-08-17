# Evaluation summary

Corpus: 33 notes. Gold set: 30 queries, judged at note level. Cutoff k = 5.
Embeddings: sentence-transformers/all-MiniLM-L6-v2.

Index: the local exact-cosine backend, so retrieval quality here is the ceiling an
approximate index would be trying to reach, and the latencies are not comparable with a
hosted service over the network. The index size column is the vector index; the BM25 model
is rebuilt in memory and stores nothing on disk. Each query is timed as the fastest of
three identical runs, taken after a short warm-up.

| chunk | method   | chunks | P@k   | R@k   | MRR   | nDCG@k | median ms | p95 ms | index MB |
|-------|----------|--------|-------|-------|-------|--------|-----------|--------|----------|
| 128   | semantic | 98     | 0.253 | 0.906 | 0.867 | 0.843  | 3.1       | 3.5    | 0.22     |
| 128   | keyword  | 98     | 0.233 | 0.856 | 0.868 | 0.828  | 0.1       | 0.1    | 0.22     |
| 256   | semantic | 65     | 0.247 | 0.894 | 0.889 | 0.856  | 3.1       | 3.3    | 0.17     |
| 256   | keyword  | 65     | 0.267 | 0.933 | 0.882 | 0.866  | 0.0       | 0.1    | 0.17     |
| 512   | semantic | 33     | 0.253 | 0.911 | 0.942 | 0.893  | 3.0       | 3.3    | 0.10     |
| 512   | keyword  | 33     | 0.247 | 0.872 | 0.883 | 0.856  | 0.0       | 0.1    | 0.10     |

## Per-query wins (reciprocal rank, semantic against keyword)

| chunk | semantic wins | keyword wins | tied |
|-------|---------------|--------------|------|
| 128   | 4             | 5            | 21   |
| 256   | 5             | 5            | 20   |
| 512   | 4             | 3            | 23   |

## By query type

Every gold query is labelled paraphrase, exact-token or lookup in goldset.yaml, and this is
the split the proposal set out to test. The aggregate table above is close to a tie, so it
is this breakdown rather than the means that answers the research question. The counts are
small once thirty queries are cut three ways, so read the direction of each row rather than
the third decimal place. Chunk size 512 is shown because it has the best semantic recall.

| category    | method   | n  | P@k   | R@k   | MRR   | nDCG@k |
|-------------|----------|----|-------|-------|-------|--------|
| paraphrase  | semantic | 10 | 0.300 | 0.833 | 0.875 | 0.788  |
| paraphrase  | keyword  | 10 | 0.240 | 0.617 | 0.700 | 0.613  |
| exact-token | semantic | 8  | 0.225 | 0.938 | 0.938 | 0.913  |
| exact-token | keyword  | 8  | 0.250 | 1.000 | 1.000 | 0.990  |
| lookup      | semantic | 12 | 0.233 | 0.958 | 1.000 | 0.968  |
| lookup      | keyword  | 12 | 0.250 | 1.000 | 0.958 | 0.968  |

At chunk size 512, semantic leads on paraphrase queries by 0.175 MRR, keyword leads on
exact-token queries by 0.062 MRR, and semantic leads on lookup queries by 0.042 MRR.

## Reading this

Recall@k is the primary metric: most queries have one or two relevant notes, so it answers
the question a user actually asks, which is whether the note they wanted is on the first
screen. P@5 is capped by the number of relevant notes a query has, so it looks low by
construction and only the comparison between rows means anything. The win counts matter as
much as the means: thirty queries is a small sample and a couple of large per-query margins
can carry an average on their own.

Regenerate with: make eval
