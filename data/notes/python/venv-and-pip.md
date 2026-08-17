---
title: Virtual environments, pip, and the errors around them
tags: [python, tooling, setup]
---

# Virtual environments, pip, and the errors around them

Setting the project up on the lab machines took longer than writing the first module, so
these are the notes for the group.

## The error everyone hits first

Homebrew's Python refuses a global install:

```
error: externally-managed-environment
```

This is PEP 668. The system marks its interpreter as managed by the OS package manager and
pip declines to touch it. The correct answer is a virtual environment, not
`--break-system-packages`, whatever the top Stack Overflow answer says.

```
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Always `python -m pip` rather than bare `pip`. A bare `pip` is whatever the shell hash
table found first, which after switching environments is often the wrong one, and you get
packages installed somewhere invisible to the interpreter you are running.

## Downloads and caching

torch is the big one. On macOS the CPU wheel is around 200MB and sentence-transformers
pulls it in transitively along with transformers, tokenizers and huggingface-hub. On a
slow connection this is a ten-minute install and it is worth warning the marker about in
the README.

Model weights are cached under `~/.cache/huggingface/hub`. First run downloads about 80MB
for MiniLM; after that it works offline. Setting `HF_HUB_OFFLINE=1` makes it fail loudly
instead of hanging when there is no network, which is what you want in a demo.

Pin nothing beyond a lower bound in requirements.txt for a project this size. A lockfile
would be more correct and is more ceremony than the module needs; I will say that in the
limitations rather than pretend it was not a choice.
