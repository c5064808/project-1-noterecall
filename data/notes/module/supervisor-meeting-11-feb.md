# Supervisor meeting, 11 February

Present: me, Priya, Tom. Twenty minutes, room 9134.

Went in with the proposal draft. The main criticism was that we had written a features
list rather than a research question. "Build a semantic search tool" is not something that
can be answered, only delivered. Rewrote it during the meeting as two questions: does
dense retrieval beat BM25 on a personal notes corpus, and how does chunk size affect
retrieval quality. Both are measurable with what we already planned to build.

Second point, which stung a bit: the scope was too large. We had a language model
summarising retrieved passages. She pointed out that the moment a model generates text the
whole evaluation changes, because we would then have to evaluate faithfulness of the
generated summary, and that is a project on its own. Cutting generation entirely means
every result is a verbatim span from the notes, which makes the no-hallucination claim
trivially true instead of something we would have to defend. Agreed to cut it. Tom is
updating the proposal.

Third, she wants the gold set written and frozen before we start tuning anything. Obvious
in hindsight. If we look at results and then adjust the queries we have fitted the
evaluation to the system.

Asked about Pinecone and the free tier. She was relaxed about it as long as the project
also runs without it, because the marker may not want to create an account, and because
part of our argument is about keeping personal notes local.

Actions before next meeting on the 25th:
- Priya: literature review skeleton, ten sources minimum, focus on dense retrieval since
  DPR.
- Tom: revised proposal with the two research questions at the front.
- Me: corpus and evaluation harness, plus the gold set.

She also said not to leave the write-up until the code is finished, which everyone says
and nobody does.
