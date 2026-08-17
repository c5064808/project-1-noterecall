# Why close-enough vector lookup is fast

Notes to self after the Tuesday lab, written in my own words because the lecture slides
used the formal terms and I want to check I actually follow the idea.

The naive way to find which stored arrow points most nearly the same way as my query
arrow is to check all of them. Every single one. That cost grows straight in line with
how much you have stored, so at some size it stops being viable in a web request.

The trick everybody uses is to accept a slightly wrong answer. You do not need the single
best match, you need matches that are good enough that a person reading the result cannot
tell the difference. Once you allow that, you can skip most of the collection.

Two ways of skipping I understood from the lab:

The first builds a web of shortcuts between stored items, where each item knows a handful
of others that sit close to it, plus a few long-range links. You drop into the web at some
arbitrary point and keep hopping to whichever neighbour is more similar to the query,
until no hop improves things. That lands you in roughly the right region without ever
looking at the far side of the collection. How many hops you are willing to keep in play
is a dial: turn it up, get better answers, wait longer.

The second groups everything into buckets first, keeps one representative arrow per
bucket, and at query time only opens the few buckets whose representative looks promising.
The obvious failure mode is a query that lands on a bucket boundary, where the true best
match sits just inside a bucket you never opened. Opening more buckets fixes it and costs
time. Same dial, different shape.

So both are the same bargain: spend a bit of build time and a bit of accuracy, buy back a
lot of query time. That is the whole idea and I think I was overcomplicating it.
