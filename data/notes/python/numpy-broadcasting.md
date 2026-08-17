---
title: Numpy broadcasting and the shape errors it causes
tags: [python, numpy, debugging]
---

# Numpy broadcasting and the shape errors it causes

Broadcasting rules, right to left: dimensions are compatible if they are equal or one of
them is 1. Missing leading dimensions are treated as 1. A (1000, 384) matrix and a (384,)
vector therefore combine fine, which is what makes the whole index a one-liner.

The error I lost most of an afternoon to:

```
ValueError: could not broadcast input array from shape (384,) into shape (768,)
```

That was an old saved index built with mpnet while the config had switched back to MiniLM.
Nothing checked that the stored matrix and the live embedder agreed on dimension. Fix was
to record the dimension in the index sidecar JSON and fail with a readable message telling
you to rebuild, instead of letting numpy complain about shapes.

The other one, which is more embarrassing:

```
ValueError: operands could not be broadcast together with shapes (1000,384) (1000,)
```

That is a norm vector without `keepdims=True`. `np.linalg.norm(mat, axis=1)` gives (1000,)
and numpy tries to align it against the last axis, which is 384. With
`keepdims=True` you get (1000, 1) and the division does what you meant.

Useful things I want to remember:

`np.argpartition(sims, -k)[-k:]` finds the top k without a full sort, then sort just those
k. Worth it above a few thousand rows, pointless below, and I used it anyway because it
reads no worse.

`np.einsum` is clearer than a chain of transposes once there are three or more axes, and
you can write the whole cosine computation as `np.einsum("ij,j->i", mat, q)`. Slower than
plain `@` for this shape though, so I did not keep it.

`float32` everywhere. The default float64 doubles the index file for no measurable gain in
ranking, and Pinecone stores float32 regardless.
