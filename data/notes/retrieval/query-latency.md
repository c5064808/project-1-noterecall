---
title: Measuring query latency honestly
tags: [retrieval, benchmarking, stats]
---

# Measuring query latency honestly

Things I got wrong the first time I timed the search loop.

Reporting the mean. Latency distributions have a long right tail, so the mean sits
somewhere nobody experiences. Report the median for the typical case and p95 for the
tail. If I have space, a small table of median / p95 / max per configuration.

Not warming up. The first query pays for lazy imports, the model weights moving into
memory, and numpy allocating its scratch buffers. On my laptop the first call was about
forty times the median. Run a handful of throwaway queries before starting the clock.

Timing the wrong thing. Encoding the query and searching the index are separate costs and
they scale differently. The MiniLM forward pass is fixed, roughly the same for any short
query; the index search grows with the collection. Bundling them hides which one you are
actually measuring. For the report I time the whole user-visible call but say clearly
that the encode step dominates at this corpus size.

Using `time.time`. Use `time.perf_counter`, it is monotonic and has better resolution.

The comparison that is not fair, and I need to be upfront about this: our local backend
does an exact brute-force cosine over a few thousand vectors, and Pinecone does
approximate search over a network. Comparing their latencies measures the round trip to
us-east-1, not the quality of anyone's algorithm. Any timing table involving Pinecone has
to be labelled as including network time, or left out.

Timer boilerplate I keep reusing:

```python
t0 = time.perf_counter()
hits = searcher.search(q, top_k=5)
elapsed_ms = (time.perf_counter() - t0) * 1000
```

TODO: check whether torch is grabbing all the cores during the timing loop and skewing it.
