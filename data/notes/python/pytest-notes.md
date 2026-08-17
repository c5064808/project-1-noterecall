# Pytest habits worth keeping

Plain `assert` and pytest rewrites it so the failure output shows both sides. No
`assertEqual`, no test classes unless there is shared state that genuinely wants a class.

`tmp_path` is a per-test `pathlib.Path` in a fresh directory, cleaned up afterwards. It is
the answer to almost every "this test writes files" problem, and it means the local index
tests can build a real index on disk rather than mocking the file layer. Mocking the file
layer would have tested the mock.

```python
def test_index_round_trips_through_disk(tmp_path):
    idx = LocalIndex(tmp_path / "idx")
    idx.ensure_ready(4)
    idx.upsert(["a#0"], np.eye(4, dtype="float32")[:1], [{"note_id": "a.md"}], "chunk256")
    reopened = LocalIndex(tmp_path / "idx")
    assert reopened.query(np.eye(4, dtype="float32")[0], 1, "chunk256")[0].chunk_id == "a#0"
```

Name tests as sentences. `test_overlap_carries_tokens_between_chunks` tells you what broke
from the summary line alone; `test_chunking_2` tells you to go and read the file.

`pytest.approx` for floats. `assert score == approx(0.5, abs=1e-6)`. Comparing floats with
`==` works right up until the day it does not.

`pytest.raises(ValueError, match="overlap")` checks both the type and that the message is
the one you meant, which stops a test passing because some unrelated ValueError fired
earlier in the call.

`-q` for a quiet run, `-x` to stop at the first failure, `-k name` to select by substring,
`--lf` to rerun only what failed last time. Those four cover nearly everything.

How many tests: enough that a real mistake is caught, not so many that changing an
interface means rewriting an afternoon of assertions. For this project that is around ten,
concentrated on chunk boundary behaviour and the metric formulas, because those are the
parts where a silent error would corrupt the results table without anything crashing.
