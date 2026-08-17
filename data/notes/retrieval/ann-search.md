---
title: Approximate nearest neighbour search
tags: [retrieval, ann, hnsw, week3]
---

# Approximate nearest neighbour search

Exact search over a vector set means comparing the query against every stored vector.
With 384 dimensions and a few thousand chunks that is one matrix multiply and it is
instant, so for this project exact search is genuinely fine. The interesting part is what
happens at a hundred million vectors, which is the regime the ANN literature is written
for.

The trade made by approximate nearest neighbour search is simple: give up the guarantee
that you found the true top-k, and in exchange only touch a small fraction of the data.
Quality is then measured as recall against the exact answer, usually recall@10, and you
tune a parameter until recall is around 0.95 and the latency is acceptable.

## The two families that matter

HNSW builds a layered proximity graph. The top layer is sparse and covers long distances,
lower layers get denser. A query enters at the top, greedily walks towards the query
vector, drops a layer, walks again. The parameter `efSearch` controls how many candidates
the walk keeps alive: raise it and recall goes up and so does latency. Build cost and
memory are high because every node stores its edge list.

IVF (inverted file) instead clusters the vectors with k-means into a few thousand lists,
stores each vector in the list of its nearest centroid, and at query time only scans the
`nprobe` closest lists. Cheaper to build than HNSW, usually a bit worse at the same
recall. Often paired with product quantisation, which compresses each vector into a short
code so that far more of the index fits in RAM.

Pinecone does not tell you which of these it runs, which is a bit annoying for a report
but is the point of a managed service.

TODO: check whether the Malkov HNSW paper reports recall@1 or recall@10 in figure 5, I
think I quoted the wrong one in the draft.
