---
title: Chunking strategies
tags: [retrieval, chunking, experiment]
---

# Chunking strategies

The unit you index is not the document, it is the chunk, and picking the chunk is the
decision with the largest effect on results for the least amount of code.

Fixed-size windows with overlap is the baseline everybody uses. Pick a window in tokens,
slide it forward by window minus overlap, emit each window. Overlap exists so that a
sentence which straddles a boundary still appears whole in one of the two chunks. Without
it you get a distinctive failure where the answer is split across the seam and neither
half scores well.

Structural chunking splits on markdown headings or paragraph breaks instead. It respects
the author's own idea of where a topic ends, which is appealing for notes, but it produces
wildly uneven chunk lengths, and a one-line heading section becomes a chunk with almost no
signal in it.

## The size trade-off, as far as I can tell

Small chunks (around 128 tokens) are precise. The embedding is dominated by one idea, so
when it matches, it matches for the right reason. But context is lost, pronouns dangle,
and a question whose answer spans two paragraphs cannot be satisfied by any single chunk.

Large chunks (512 and up) keep context but dilute. The single vector has to represent
several topics at once and ends up near the average of them, which is near nothing in
particular. Precision drops even though the right document is still retrieved.

I expect 256 to win on this corpus, mostly because the notes themselves are short and a
256-token window is roughly one section of one note. That is a prediction, not a result,
and the evaluation is there to check it.

One cheap trick worth measuring separately: prepend the note title to every chunk before
embedding. It costs a few tokens and it gives orphaned middle chunks some idea of what
document they came from.
