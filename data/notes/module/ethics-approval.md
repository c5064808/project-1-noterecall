---
title: Ethics approval
tags: [module, ethics, admin]
---

# Ethics approval

Reference SHUREC7-2026-0417, submitted 3 February, approved 12 February. Keep the approval
email; a copy of it goes in Appendix C.

The form is the low-risk route because we are not recruiting participants and not
processing anyone else's personal data. Two things still had to be argued properly.

First, the corpus. Our original plan was to index our own real study notes, which contain
supervision discussions and, in Tom's case, notes referring to a placement employer under
NDA. The committee's concern was not that we would publish them but that the submitted
artefact is retained by the university and a marker will run it. Resolution: the submitted
repository ships a demo corpus written for the purpose, containing nothing personal, and
the tool reads whatever directory you point the notes path at. Real notes stay on our own
machines and never enter the submission.

Second, third-party processing. If vectors are sent to Pinecone, text derived from the
notes leaves the machine and lands on a US-hosted service. For the demo corpus this is
harmless, but the write-up must not claim the design is private in general when the
default cloud path is not. Resolution: the local backend is a first-class option, the
system runs end to end with no API key, and the README states plainly which mode sends
data where.

No participants means no consent forms, no debrief, and no data management plan beyond
"do not commit the real notes". The `.gitignore` covers the local index directory and any
`.env` file with a key in it.

If we later interview anyone about usability, that is a new application, not an amendment.
Would need a participant information sheet and consent forms, and realistically two weeks
of turnaround, which we do not have. So the evaluation stays offline and metric-based.
