---
title: Hypothesis testing refresher
tags: [stats, week5]
---

# Hypothesis testing refresher

Refresher before the methods chapter, because I want to say something defensible about
whether semantic search beats BM25 rather than just pointing at two numbers.

The null hypothesis is the boring explanation: the two systems are equally good and the
gap we see is the luck of which thirty queries we happened to write. A p-value is the
probability of seeing a gap at least this large if the boring explanation were true. It is
not the probability that the boring explanation is true, and the number of published
papers that get this backwards is unnerving.

Because both systems answer the same queries, the comparison is paired, and a paired test
has far more statistical power than an unpaired one: the per-query difficulty cancels out.
So the unit of analysis is the per-query difference in the metric, not the two averages.

For thirty paired observations of a metric like reciprocal rank, which is bounded, lumpy
and nothing like normal, the paired t-test's assumptions are shaky. Better options are
the Wilcoxon signed-rank test, which only assumes a symmetric distribution of differences,
or a permutation test, which assumes almost nothing: randomly swap the two systems'
results within each query a few thousand times and see where the real difference falls in
that distribution.

With thirty queries the test is underpowered for anything but a large effect. If the
result comes out non-significant, the honest sentence is "we could not detect a
difference at this sample size", not "there is no difference".

Multiple comparisons: three chunk sizes times two methods times four metrics is a lot of
opportunities to find something at p < 0.05 by accident. Decide the primary metric before
looking, report the rest as descriptive. I am picking recall@5 as primary.
