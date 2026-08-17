# Presentation plan

Fifteen minutes, three of us, five minutes of questions after. Rough split at three
slides a minute is too fast; twelve slides total is the target.

1. Title and the problem in one sentence. You can never find the note you know you wrote,
   because you remember the idea and not the words. (Tom, 1 min)
2. Research questions. Both on one slide, big text. (Tom, 1 min)
3. Related work in three bullets: BM25, dense retrieval, and the BEIR finding that dense
   is not automatically better out of domain. (Priya, 3 min)
4. System diagram. Notes, chunker, embedder, index, query path. One arrow per stage, no
   clip art. (Priya, 2 min)
5. The deliberate absence of a language model, and why that makes the no-fabrication claim
   trivial rather than a promise. This is our strongest slide. (Priya, 1 min)
6. Method: corpus, gold set, metrics, the three chunk sizes. (me, 2 min)
7. Results table. (me, 2 min)
8. One example where semantic wins and one where keyword wins, actual screenshots. Worth
   more than the table for an audience. (me, 2 min)
9. Limitations, honestly. (me, 1 min)

Live demo: no. Rehearse it, record a thirty second screen capture, play that. Wifi in
the seminar rooms is not worth the risk and the first query pays for model loading anyway.

Anticipated questions and who takes them:
- "Why not use a language model?" Priya, this is our set piece.
- "Is thirty queries enough?" Me. Answer honestly: no, it detects direction not size.
- "Why Pinecone if the local index works?" Tom, scale argument plus the coursework
  requirement to use a managed vector store.
- "How would this handle a hundred thousand notes?" Me. Exact search stops being viable
  somewhere around a million chunks on one machine.

TODO: book a practice slot. Last time we ran four minutes over.
