# Profiling: cProfile, snakeviz, timeit

Rule I keep forgetting and then relearning: measure before optimising, because the
bottleneck is never where I guessed.

`cProfile` is in the standard library and gives deterministic per-function timings with a
few percent of overhead on ordinary code, much more on code with millions of tiny calls.

```
python -m cProfile -o profile.out -m noterecall index --chunk-size 256
snakeviz profile.out
```

`snakeviz` renders the pstats file as an icicle plot in the browser and is far easier to
read than `pstats.Stats.sort_stats("cumulative").print_stats(20)`, though that one line is
what I use over ssh.

Read cumulative time first to find the branch of the call tree that costs, then total time
inside that branch to find the function actually burning the cycles.

What the profile said about our indexing run, which was not what I expected: the model
forward pass was around 80 percent, reading and chunking the markdown was under 2 percent,
and about 12 percent was in tokenisation inside sentence-transformers, not in torch. So
optimising the chunker would have been completely pointless. The only lever that matters
is batch size and how many texts we send.

`timeit` for microbenchmarks, and use it through the module interface so it disables the
garbage collector and takes the minimum of several runs rather than the mean, which is the
right statistic when you are measuring a lower bound corrupted by noise.

For wall-clock in application code, `time.perf_counter`. Never `time.time`, which can go
backwards when the clock is adjusted.

A profiler cannot see time spent waiting on the network, which will matter if we ever
profile the Pinecone path; it will look almost free and it will not be.
