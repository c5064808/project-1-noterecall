---
title: How many dimensions do you need
tags: [embeddings, dimensionality]
---

# How many dimensions do you need

384 versus 768 versus 1536. The received wisdom is bigger is better and the received
wisdom is only about half right.

What extra dimensions buy you is room to keep things apart. Johnson-Lindenstrauss says
that to preserve pairwise distances within a factor of epsilon you need on the order of
log(n) / epsilon squared dimensions, which for a million items and 10 percent distortion
lands somewhere in the low thousands. That bound is worst-case over arbitrary point sets;
real text embeddings live on a much lower dimensional surface inside the space, so the
practical requirement is far smaller.

What extra dimensions cost is linear in everything. Storage, memory, the matmul at query
time, the network payload. Going from 384 to 768 doubles the index size and roughly
doubles brute-force query time. For a personal notes corpus of a few thousand chunks that
is the difference between two milliseconds and four, so it does not matter at all here;
at a hundred million vectors it is the difference between one machine and two.

On MTEB the 768-dim mpnet model beats the 384-dim MiniLM by a few points of average nDCG.
A few points is real but it is not the difference between working and not working, and
the CPU cost is roughly five times. For this project MiniLM is the right call and I should
say so as a decision with a reason rather than a default I never questioned.

Matryoshka embeddings are the interesting recent idea: train so that the first 64 or 128
components are usable on their own, then truncate per use case. Retrieve with the short
prefix, rerank with the full vector. Filed under things I would try with more time.
