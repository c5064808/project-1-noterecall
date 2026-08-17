# Argparse with subcommands

For a tool with an index / search / stats shape, subparsers are the right structure and
the API is fiddly enough that I keep re-deriving it.

```python
parser = argparse.ArgumentParser(prog="noterecall")
sub = parser.add_subparsers(dest="command", required=True)

p_index = sub.add_parser("index", help="embed the notes and build the index")
p_index.add_argument("--chunk-size", type=int, action="append")
p_index.add_argument("--rebuild", action="store_true")

p_search = sub.add_parser("search")
p_search.add_argument("query")
p_search.add_argument("--top-k", type=int, default=5)
```

`dest="command"` is what tells you afterwards which subcommand ran. `required=True` is
needed on 3.7 and later or bare `noterecall` falls through with `command=None` and you
get an AttributeError instead of a usage message.

`action="append"` with a default is the trap. If you write `default=[256]` and the user
passes `--chunk-size 128`, you get `[256, 128]`, because append adds to the default list
rather than replacing it. The fix is `default=None` and substituting the default after
parsing.

`set_defaults(func=cmd_index)` on each subparser, then `args.func(args)` in main, is the
tidy dispatch. I did that at first and then unwound it, because with three commands an
if/elif chain is shorter and a reader does not have to chase an attribute to find the
handler.

Return an int from main and pass it to `sys.exit`, so failures give a non-zero status and
`make` notices. Print errors to stderr; a one-line message beats a traceback for anything
the user can actually fix, like an index that has not been built yet.

Why not click or typer: two fewer dependencies, and nothing here needs more than argparse
provides. Fewer moving parts to justify in the report.
