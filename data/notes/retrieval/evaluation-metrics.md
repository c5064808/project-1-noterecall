# Ranking metrics for the evaluation chapter

Definitions written out properly so I stop guessing at them in the write-up.

Precision@k is the fraction of the top k results that are relevant. With k = 5 and two
relevant documents returned, P@5 = 0.4. Note the ceiling problem: if a query only has one
relevant document in the whole collection, P@5 can never exceed 0.2, so averaging P@5
across queries with different numbers of relevant documents is not comparing like with
like.

Recall@k is the fraction of all relevant documents that made it into the top k. With one
relevant document and it appearing anywhere in the top 5, R@5 = 1.0. For a small gold set
where most queries have one or two right answers, recall@5 is the metric that behaves
most sensibly.

Reciprocal rank is 1 divided by the position of the first relevant result, 0 if none
appear. Mean reciprocal rank averages that over queries. It only looks at the first hit,
which is exactly right for a search box where the user reads the top result and stops.

nDCG@k discounts each relevant hit by log2 of its position plus one, sums that, and
divides by the best achievable sum for that query. With binary relevance the ideal DCG is
the sum over the first min(k, number of relevant) positions. A single relevant document
found at rank 3 gives DCG = 1/log2(4) = 0.5 and IDCG = 1, so nDCG@5 = 0.5. That worked
example is the one to put in the tests.

Practical points for our setup. Relevance is judged per note, not per chunk, so the ranked
list has to be deduplicated by note before scoring, otherwise five chunks from one note
look like five separate correct answers. And the gold set is written by us, over our own
notes, which is a real threat to validity that belongs in the limitations section rather
than being quietly ignored.
