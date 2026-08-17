# Cosine similarity versus dot product

The dot product of two vectors is the sum of the elementwise products. Cosine similarity
is that same dot product divided by both magnitudes, which removes length and leaves only
direction. So cosine is the dot product of the L2-normalised vectors, and if you normalise
once at index time the two metrics give identical rankings and you get the cheaper one for
free.

That equivalence is worth stating carefully because it is the reason the local index can
be a single matmul. Normalise the matrix rows when they go in, normalise the query, then
`matrix @ query` is a vector of cosine similarities and `argpartition` picks the top k.

When does the difference matter? When magnitude carries information. Some models let
vector length encode confidence or term frequency, and there dot product rewards
documents the model is confident about, while cosine treats a hesitant match and a certain
one alike. For sentence transformers trained with a cosine objective, the magnitude means
nothing, so cosine is the right choice and dot product on unnormalised vectors is a bug
waiting to happen.

Euclidean distance on normalised vectors is monotonically related to cosine as well:
d squared equals 2 minus 2 cos. Same ranking, reversed order. So all three of the usual
metrics collapse to the same thing once everything is unit length, and the only real
decision is whether to normalise.

Pinecone makes you fix the metric at index creation and will not let you change it, so
this is a decision you make once and live with. Cosine.

```python
mat /= np.linalg.norm(mat, axis=1, keepdims=True)
sims = mat @ query_vec
```

Watch out for the zero vector, which is what you get from an empty chunk. Dividing by a
zero norm gives NaN and NaN propagates through argpartition in a way that is confusing to
debug. Filter empty chunks before embedding rather than patching it afterwards.
