---
title: Sentence transformers and all-MiniLM-L6-v2
tags: [embeddings, models, minilm]
---

# Sentence transformers and all-MiniLM-L6-v2

A plain BERT encoder gives you one vector per token and its CLS vector is not, despite
what everyone assumes, a usable sentence representation out of the box. Sentence
transformers fix that by fine-tuning with a pooling layer on top and an objective that
puts similar sentences near each other.

all-MiniLM-L6-v2 in numbers: 6 transformer layers, hidden size 384, about 22 million
parameters, maximum sequence length 256 word pieces, mean pooling over the token outputs,
and the released model already L2-normalises its output. Roughly 80MB on disk. It runs on
CPU at a few hundred short sentences a second on this laptop, which is why it is the
default for anything that needs to be reproducible without a GPU.

## The truncation trap

The 256 token limit is the one that catches people. Anything past it is silently
truncated, no warning. If a chunk is 512 whitespace tokens, and word-piece tokenisation
expands technical text by roughly a third, the tail of that chunk never reaches the model
at all. That is a confound in the chunk size experiment and it needs saying in the
write-up: at 512 we are not really comparing 512 tokens of context, we are comparing
"about 256 word pieces plus some discarded text".

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
vecs = model.encode(texts, batch_size=64, normalize_embeddings=True,
                    convert_to_numpy=True)
```

Bigger alternatives if we had the budget: all-mpnet-base-v2 is 768-dim and clearly better
on the MTEB retrieval tasks but around five times slower on CPU, and the e5 family wants
"query: " and "passage: " prefixes which changes the code path. Not worth the complexity
for a module project. Noting them as future work.
