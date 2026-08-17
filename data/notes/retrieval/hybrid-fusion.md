# Combining two rankings without tuning weights

The obvious way to combine a dense ranking and a keyword ranking is a weighted sum of
their scores. It does not work well without effort, because the two score scales are not
comparable: cosine similarity sits in a narrow band around 0.3 to 0.7, BM25 scores are
unbounded and depend on the query length and the collection. You end up fitting a weight
per query type and pretending that generalises.

Reciprocal rank fusion sidesteps this by throwing the scores away and using only the
positions. Each document gets sum over runs of 1 / (k + rank), with rank starting at 1 and
k a constant, conventionally 60. Sort by that sum.

```python
scores = defaultdict(float)
for run in runs:
    for rank, hit in enumerate(run, start=1):
        scores[hit.chunk_id] += 1.0 / (k + rank)
```

Why k = 60: it flattens the difference between the top few positions so that a document
ranked 1 by one system and 8 by the other beats a document ranked 3 by one system and
absent from the other. Small k makes the top position dominate; large k makes everything
nearly equal and the fusion degenerates into counting how many systems returned the
document at all.

What I like about it is that there is nothing to train and nothing to calibrate, which
means it cannot quietly overfit the thirty queries in our gold set. What I do not like is
that it discards genuine information: a keyword match with an enormous score because the
query token appears in exactly one document deserves more than a rank-1 slot's worth of
credit.

For the report this stays a secondary result. The research question is dense versus
sparse, and hybrid is the "yes, obviously, you would combine them in practice" footnote.
If it wins on both metrics it is still worth a paragraph.
