---
title: Vector databases and Pinecone
tags: [retrieval, pinecone, infrastructure]
---

# Vector databases and Pinecone

A vector database is a store whose primary key lookup is "give me the k rows whose vector
is most similar to this one". Everything else it does, filtering, namespaces, metadata,
exists to make that one operation useful in an application.

Pinecone specifics I keep forgetting:

- Serverless indexes are created with a cloud and a region, e.g. aws and us-east-1. The
  free tier only allows certain regions, us-east-1 is the safe choice.
- Creation is asynchronous. After `create_index` you have to poll until the status
  reports ready, otherwise the first upsert fails.
- `upsert` takes a list of records, each with an id, values and metadata. Batches of 100
  are the documented recommendation. Larger batches hit the 2MB request limit quickly if
  the metadata carries text.
- There is a per-vector metadata size limit of 40KB, so storing the whole chunk text in
  metadata only works if you truncate it. I truncate to 1500 characters.
- `describe_index_stats` returns the vector count per namespace. That is the call to use
  in the stats command, and it is also the cheapest way to confirm an upsert actually
  landed rather than being silently accepted.
- Namespaces partition an index. Queries never cross a namespace, which makes them a neat
  way to hold three chunk-size variants of the same corpus side by side.

```python
res = index.query(vector=q.tolist(), top_k=5, namespace="chunk256", include_metadata=True)
for m in res["matches"]:
    print(m["id"], round(m["score"], 3))
```

The metric has to be chosen at creation and cannot be changed. Cosine for normalised
sentence embeddings.

One honest limitation for the write-up: the moment vectors leave the machine, the privacy
argument for searching your own notes gets weaker. Worth a paragraph in the discussion.
