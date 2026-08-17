# Is this gap real or did I get lucky

Thinking out loud after the seminar. Deliberately avoiding the technical words to check I
understand the reasoning rather than the vocabulary.

I have two versions of the search tool. On my thirty questions one scores 0.71 and the
other 0.64. The question is whether I would see the same ordering if I wrote thirty
different questions tomorrow.

The uncomfortable thing is that the questions are the sample, not the notes. Thirty is not
many. If four of my questions happen to suit one method, that alone can swing the average
by more than the gap I am excited about. So the gap has to be compared against how much
the average wobbles when the question set changes.

Two ways to get a feel for the wobble without any maths:

Look at the questions one at a time. Line up both scores per question and count how often
each method wins. Twenty-two wins out of thirty is a different story from sixteen out of
thirty even if the averages are identical, because the second one means a couple of
questions with big margins are carrying everything.

Then, pretend I only had a random two thirds of the questions, recompute, and do that over
and over. If the winner flips on a decent share of those pretend question sets, I do not
have a finding, I have noise with a nice mean.

What I want to avoid is the write-up that says "our method achieved a 7 point improvement"
full stop. That sentence is true and useless. The version I want is: it won on 22 of 30
questions, the ones it lost were all short exact-token lookups, and with a set this small
the size of the improvement should not be taken seriously even though its direction
probably should.

Also worth writing down: I chose the questions after reading my own notes. That is a
bigger threat to the result than any amount of arithmetic about wobble.
