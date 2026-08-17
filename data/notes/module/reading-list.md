# Reading list for the literature review

Core, all read:

Karpukhin et al. 2020, Dense Passage Retrieval for Open-Domain Question Answering. The
paper that made dense retrieval respectable: a dual encoder trained on question-passage
pairs beats BM25 by a wide margin on top-20 accuracy. Bibtex key in our file is
`karpukhin2020dpr`. Their in-batch negatives section is the one to cite for the training
discussion.

Robertson and Zaragoza 2009, The Probabilistic Relevance Framework: BM25 and Beyond. The
proper source for BM25 rather than a blog post. Long, but sections 3 and 4 are what we
need.

Reimers and Gurevych 2019, Sentence-BERT. Justifies why we use a sentence encoder rather
than cross-encoding every pair: cross-encoders are better and computationally impossible
for search over anything sizeable.

Malkov and Yashunin 2018, HNSW. Cite for the graph index, and be careful about which
recall figure I quote.

Thakur et al. 2021, BEIR. The important counterweight to DPR: on out-of-domain
benchmarks BM25 is competitive with and often beats dense models. Given our corpus is
nothing like anyone's training data, this is directly relevant and should temper how
confident the discussion sounds.

Cormack et al. 2009, Reciprocal Rank Fusion. Short, one good idea, cite it for the hybrid
mode.

To read:

- Izacard et al. 2022, Contriever, unsupervised dense retrieval.
- Formal et al. 2021, SPLADE, learned sparse retrieval, sits neatly between our two arms.
- Something on chunking. I cannot find a peer-reviewed source; everything is engineering
  blogs, which is awkward for the review. Ask the librarian.

Ten sources minimum for the review. This is thirteen if the "to read" three get done.
