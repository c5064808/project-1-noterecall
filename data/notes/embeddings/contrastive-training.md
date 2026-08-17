# Contrastive training, in-batch negatives

How a sentence encoder learns that a question and its answer belong together.

You need pairs. Question and accepted answer, title and body, caption and image, two
translations of the same line. The model encodes both sides and the loss pushes the pair
together and pushes everything else apart. The everything else is where the trick is.

Sampling explicit negatives is expensive and mostly wasted, because a randomly chosen
negative is so obviously wrong that the model learns nothing from it. In-batch negatives
solve this for free: inside a batch of B pairs, treat the other B-1 right-hand sides as
negatives for each left-hand side. One forward pass gives you B positives and B(B-1)
negatives. This is why contrastive training likes enormous batches, and why the reported
numbers move when people change batch size, which makes reproduction annoying.

The loss is softmax cross entropy over similarities scaled by a temperature, usually
called InfoNCE or multiple-negatives ranking loss. Low temperature sharpens the
distribution and makes the model obsess over the hardest negative in the batch; too low
and it becomes unstable.

Hard negative mining is the next step up. Retrieve with the current model, take the
top-ranked wrong answers, feed those in as explicit negatives. It clearly helps and it
also introduces false negatives, because "wrong answer" in your labels often means
"unlabelled correct answer", and training against those actively damages the model. The
DPR paper has a section on this.

Consequence for us: all-MiniLM-L6-v2 was trained on around a billion mostly web-derived
pairs, none of which look like a postgraduate student's shorthand lecture notes. Domain
mismatch is a plausible explanation for anything odd in the results and is worth a
sentence in the discussion instead of hand-waving.
