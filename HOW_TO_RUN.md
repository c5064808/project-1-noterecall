# How to run this project, step by step

This is the short version. It assumes you have just unzipped the folder and have nothing
installed. Follow the steps in order. Each step says what you should see when it works.

The README has the detail and the design reasoning. This file just gets it running.

**You do not need to download any data.** The notes this project searches are already
inside the folder, in `data/notes`. There are 33 of them.

**You do not need any API key.** Nothing in this project talks to a paid service.

---

## Step 1 — Check you have Python

Open a terminal, go into this folder, and type:

    python3 --version

You should see `Python 3.10` or higher, for example:

    Python 3.12.13

If the command is not found, or the number is lower than 3.10, install Python from
<https://www.python.org/downloads/> and then close and reopen the terminal.

---

## Step 2 — Make a virtual environment

This keeps the project's packages separate from the rest of your computer.

    python3 -m venv .venv
    source .venv/bin/activate

On Windows the second line is `.venv\Scripts\activate` instead.

Your terminal prompt should now start with `(.venv)`. That is how you know it worked.

---

## Step 3 — Install the packages

    pip install -r requirements.txt

This takes a while, five to fifteen minutes on a normal connection, because it downloads
PyTorch which is around 2 GB. Let it finish.

You should see a long list of packages and then `Successfully installed ...` at the end.

---

## Step 4 — Build the search index

    python -m noterecall index

The first time you run this it also downloads the embedding model, about 80 MB. After
that it works offline.

Expected output:

    Loaded 33 notes from .../data/notes
    Embedding with sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) into the local index
    chunk256: 65 chunks, embedded in 0.2s, stored in 0.0s

    Index stats
      backend: local
      directory: .../.index
      total_vector_count: 65
        chunk256: vector_count=65, dimension=384, size_mb=0.095

The timings will differ on your machine. What matters is that it loads 33 notes and
finishes without an error.

If you also want the other two chunk sizes, which the evaluation uses:

    python -m noterecall index --chunk-size 128 --chunk-size 256 --chunk-size 512

---

## Step 5 — Search the notes

    python -m noterecall search "cutting a long document into pieces before indexing it"

Expected output:

    semantic search over chunk256, top 5

     1   0.547  Chunking strategies  (retrieval/chunking-strategies.md)
              Chunking strategies is near nothing in particular. Precision drops even
              though the right document is still retrieved...

     2   0.540  Chunking strategies  (retrieval/chunking-strategies.md)
              ...

The point to notice: the query does not contain the words "chunk" or "chunking", and the
right note still comes back first. That is the whole idea of the project.

Now try the same query with keyword search to see the difference:

    python -m noterecall search "cutting a long document into pieces before indexing it" --mode keyword

Keyword search does much worse on this one, because it can only match words that are
actually there.

---

## Step 6 — Run the evaluation

This is the part that produces the numbers used in the report.

    python -m evaluation.run_eval

It takes about ten seconds. It runs 30 test queries through both search methods at three
different chunk sizes and writes the results to the `results` folder.

Expected output ends with a table like this:

    | chunk | method   | chunks | P@k   | R@k   | MRR   | nDCG@k |
    |-------|----------|--------|-------|-------|-------|--------|
    | 128   | semantic | 98     | 0.253 | 0.906 | 0.867 | 0.843  |
    ...

Afterwards, look in `results/`:

- `summary.md` is the readable summary
- `metrics.csv` and `metrics_by_category.csv` are the raw numbers
- `figures/` has three charts

---

## Step 7 (optional) — The web page version

    streamlit run noterecall/app.py

Your browser opens a page where you can type searches and switch between semantic and
keyword mode. Press Ctrl+C in the terminal to stop it.

---

## Using your own notes instead of the ones provided

Point the tool at any folder of markdown files. `index` takes a flag; `search` does not, so
set the `NOTES_DIR` environment variable and both commands pick it up:

    export NOTES_DIR=/path/to/your/notes
    python -m noterecall index
    python -m noterecall search "whatever you want to find"

Or per command:

    NOTES_DIR=/path/to/your/notes python -m noterecall search "whatever you want to find"

An Obsidian vault works as-is. Note that the 30 evaluation queries were written against the
notes supplied with the project, so `run_eval` only makes sense on those.

---

## If something goes wrong

**`command not found: python3`** — Python is not installed, see Step 1.

**`No module named noterecall`** — you are in the wrong folder, or the virtual environment
is not active. Check your prompt starts with `(.venv)` and that `ls` shows a `noterecall`
folder.

**`No index for namespace chunk256`** — you skipped Step 4. Run `python -m noterecall index`.

**It hangs on the first search** — it is downloading the embedding model. Wait, it only
happens once.

**A `Loading weights` progress bar appears** — that is normal, it is not an error.

**No internet at all** — everything still works after Step 4 has been run once. You can
also add `EMBEDDING_BACKEND=hashing` in front of any command to skip the model entirely,
but results get much worse and it is only meant as a smoke test.
