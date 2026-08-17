---
title: Laptop setup for the project
tags: [misc, setup, macos]
---

# Laptop setup for the project

M2 Air, 16GB, macOS. Everything below is what I actually had to do, in order, after
wiping and starting again in January.

Python from python.org rather than the system one, 3.12. Homebrew's works too but its
version moves under you when you run `brew upgrade` and that broke a venv mid-week last
term.

Torch on Apple silicon uses the MPS backend. Some operations are not implemented there
and you get an error naming the operator. The escape hatch is

```
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

which quietly runs the missing operator on CPU. For MiniLM at our batch sizes MPS is
barely faster than CPU anyway, so I left the device on CPU for the reported runs, which
also makes the timings comparable with the lab machines.

Thread thrashing was the other surprise. Torch and numpy both spin up as many threads as
there are cores and then fight over them, and the timing loop got noisy. Setting

```
export OMP_NUM_THREADS=4
```

made the median query latency stable enough to report. Worth a footnote in the evaluation
because it changes the numbers.

Model cache lives in `~/.cache/huggingface/hub`. It survives deleting the venv, so a
rebuild does not re-download 80MB. Do not put it in the repo.

Editor is VS Code with ruff, line length 100 to match what we agreed. Format on save off,
because a reformat in the middle of a shared branch is a horrible diff to review.

Time Machine to the external drive plus the repo pushed daily. Two copies of the notes
directory, neither of them in the university OneDrive, which is the ethics condition.
