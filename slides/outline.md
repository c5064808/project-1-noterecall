# NoteRecall presentation outline

Semantic Search over Personal Notes using Pinecone ANN Retrieval.
Module 55-710603. Group presentation and live demonstration.

Seventeen slides. This file is the working outline; the deck itself is `NoteRecall_Presentation.pptx`. Keep the two in step when either changes.

Every number on a slide comes from `results/summary.md, results/metrics.csv or results/metrics_by_category.csv`. Nothing on a slide is estimated, and the charts are rendered from those same files rather than drawn by hand.

## 1. NoteRecall

Open by naming the one design decision that shapes everything: there is no language model in this project. Nothing is generated, so nothing can be invented. Say we will show where semantic search wins, where it loses, and that the honest headline is that it is a tie until you split by question type.

## 2. You remember the idea, not the words

Speaker and timing: Venkat Vivek Gopisetty  •  0:00–1:30

Set the problem as a retrieval problem, not a chatbot problem. The right test of a notes search tool is whether it finds the note you were thinking of when you cannot remember how you phrased it. Read the quoted query aloud and say the target note contains none of those words.

## 3. Search by meaning, answer only by quoting

Speaker and timing: Venkat Vivek Gopisetty  •  1:30–2:30

Two things to land here. First, no generation means no hallucination, by construction rather than by evaluation. Second, the baseline runs over identical chunks, so any difference we report is attributable to scoring and nothing else.

## 4. Two paths, one index

Speaker and timing: Nithinreddy Duggireddy  •  2:30–3:30

Walk the write path along the top, then the read path along the bottom, and point out that both meet at the index in the middle. Stress that the index sits behind one protocol with two backends, so nothing above it knows or cares which is running.

## 5. Real notes are not uniform

Speaker and timing: Venkat Vivek Gopisetty  •  3:30–4:20

The title-prepending decision is worth dwelling on because it is measurable and non-obvious. Also flag the 512 row: 33 chunks from 33 notes means every note is one chunk, which matters when we read the results.

## 6. One protocol, two backends

Speaker and timing: Nithinreddy Duggireddy  •  4:20–5:10

Make the point that the protocol is what allowed the retrieval code to be written and tested before anyone had a Pinecone account. Be explicit that the local backend is exact search, so its latency is not comparable with a hosted approximate service over a network.

## 7. Making the comparison fair

Speaker and timing: Venugopal Raja  •  5:10–6:00

The fairness argument is the point of this slide. Same chunks, same return type, one difference. Mention that BM25 sometimes returns nothing while semantic never does, because that is the difference a user actually feels.

## 8. Two front ends, one search path

Speaker and timing: Mounika Maddula  •  6:00–6:40

Be straight that this component is judged differently because it produces no numbers. Its value is that the mode switch turns an abstract comparison into something an audience can see in one click, which is exactly what we will use in the demo.

## 9. Thirty queries, judged at note level

Speaker and timing: Vinay Krishna Kommalapati  •  6:40–7:40

Explain why P@5 looks low: most queries have one or two relevant notes, so a query with one right answer can never score above 0.2. Only the comparison between rows means anything. Then own the threat to validity before anyone raises it.

## 10. On the aggregate, it is a tie

Speaker and timing: Vinay Krishna Kommalapati  •  7:40–8:30

Do not rush past this slide to get to the good one. The aggregate genuinely does not settle anything, and saying so first is what makes the next slide credible. Point at the three chunk sizes giving three different winners.

## 11. The aggregate hides the whole story

Speaker and timing: Vinay Krishna Kommalapati  •  8:30–9:30

This is the slide the presentation exists for. Say the aggregate was a wash because the two effects cancel: semantic gains on paraphrases are almost exactly offset by keyword gains on exact tokens. Averaging them was the wrong thing to look at.

## 12. 512 wins, and the reason undercuts the result

Speaker and timing: Nithinreddy Duggireddy  •  9:30–10:10

Resist the temptation to present 512 as the answer. Explain that at 512 the chunker is not really chunking on this corpus, which makes that row the least trustworthy number in the table even though it is the largest.

## 13. Three things we did not expect

Speaker and timing: Venugopal Raja  •  10:10–10:50

Frame all three as things that made the report more honest rather than less impressive. The third one is the most practically useful: a method that is sometimes empty feels much worse to use than a method that is sometimes second-best.

## 14. What we did not do, and why

Speaker and timing: Mounika Maddula  •  10:50–11:20

Say the sample size limit plainly and early, because a marker will otherwise ask. The point about significance testing being theatre at n=30 shows we thought about it rather than forgot it.

## 15. The same query, both modes

Speaker and timing: Venugopal Raja  •  11:20–13:30

Run query one in semantic, then flip the mode radio and run it again. Let the audience see the note vanish. Then query two in keyword to show the honest reverse. Close with hybrid on query two if there is time.

## 16. Neither method wins. That is the result.

Speaker and timing: Venkat Vivek Gopisetty  •  13:30–14:20

End on the routing idea, because it follows directly from our own evidence rather than from a wish list. Then hand over to questions.

## 17. Questions

Leave this up during questions. If asked which method to use in production, the answer is route by query type. If asked about the corpus, concede immediately that we wrote it and that a real vault is the obvious next step.
