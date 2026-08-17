# Bootstrap confidence intervals

The idea, which felt like cheating the first time I saw it: treat the sample as if it were
the population, draw new samples from it with replacement, and look at how much your
statistic moves across those draws. That spread estimates the spread you would have seen
from repeated sampling of the real population.

Procedure for our evaluation:

1. Take the thirty per-query metric values.
2. Draw thirty of them with replacement. Some appear twice, some not at all.
3. Compute the mean of that resample.
4. Repeat a few thousand times.
5. The 2.5th and 97.5th percentiles of those means are a 95 percent percentile interval.

Two thousand resamples is plenty for an interval; ten thousand if you want a stable
p-value. It costs nothing here because the metric is already computed per query and the
resampling is just indexing into an array.

```python
rng = np.random.default_rng(0)
idx = rng.integers(0, len(vals), size=(2000, len(vals)))
means = vals[idx].mean(axis=1)
lo, hi = np.percentile(means, [2.5, 97.5])
```

For comparing two systems, resample the query indices once per iteration and compute both
systems' means on the same resampled queries, then take the difference. Resampling each
system independently throws away the pairing and inflates the interval.

Caveats. The bootstrap does not invent information: with thirty queries the interval will
be wide and it should be. It also behaves badly for statistics near a boundary, and
precision@5 with one relevant document is capped at 0.2, so its distribution is a lumpy
little thing pressed against the ceiling. Percentile intervals are the crude version; BCa
corrects for bias and skew and is what I would use if a marker pushed on it.

Seed the generator and record the seed, or the intervals move between runs and nobody can
reproduce the table.
