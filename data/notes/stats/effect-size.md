---
title: Effect size
tags: [stats, reporting]
---

# Effect size

A p-value tells you whether you can distinguish an effect from zero. It says nothing about
whether the effect is worth caring about. With enough data every difference is
significant; with little data nothing is. Effect size is the part that survives the sample
size.

Cohen's d is the difference in means divided by the pooled standard deviation. Conventional
labels: 0.2 small, 0.5 medium, 0.8 large. Those labels are Cohen's own rough guesses from
1962 and he said so himself, so quoting them as thresholds is weaker than it looks. For
paired data use the standard deviation of the differences, not the pooled one.

For ranking experiments, a raw difference in the metric is usually more informative than a
standardised one. "Recall@5 goes from 0.64 to 0.78" is directly interpretable, and any
reader can decide for themselves whether fourteen points matter for their use. A d of 0.6
means nothing to anyone without translation.

A per-query win/loss/tie count alongside the mean is the other thing I want in the table.
Means hide the shape: one query where a method scores 1.0 instead of 0.0 moves a
thirty-query mean by 0.033, and three such queries can manufacture an apparently
meaningful improvement while the method is worse on everything else.

For proportions, an odds ratio or a risk difference. Odds ratios get misread as risk
ratios constantly, especially when the base rate is high.

Confidence interval on the effect size, always. A point estimate with no interval invites
the reader to treat the third decimal place as real.

TODO: work out what a sensible smallest-worth-noticing difference is for recall@5 in a
personal search tool. My instinct is that under about 0.05 nobody would ever feel the
difference in daily use, which would make it the number to compare against.
