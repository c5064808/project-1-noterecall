from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

MARKDOWN_SUFFIXES = {".md", ".markdown"}
SKIPPED_NAMES = {"readme.md", "readme.markdown"}

FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)
H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class Note:
    note_id: str
    path: Path
    title: str
    text: str
    tags: list[str] = field(default_factory=list)


def load_notes(notes_dir: Path) -> list[Note]:
    """Read every markdown file under `notes_dir`, sorted by note_id for determinism."""
    notes_dir = Path(notes_dir)
    if not notes_dir.is_dir():
        raise FileNotFoundError(f"notes directory not found: {notes_dir}")

    notes = []
    for path in notes_dir.rglob("*"):
        if path.suffix.lower() not in MARKDOWN_SUFFIXES or path.name.lower() in SKIPPED_NAMES:
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        body, tags = _strip_front_matter(raw)
        title, body = _split_title(body, path.stem)
        if not body:
            continue
        notes.append(
            Note(
                note_id=path.relative_to(notes_dir).as_posix(),
                path=path,
                title=title,
                text=body,
                tags=tags,
            )
        )
    return sorted(notes, key=lambda note: note.note_id)


def _strip_front_matter(raw: str) -> tuple[str, list[str]]:
    match = FRONT_MATTER_RE.match(raw)
    if not match:
        return raw, []
    return raw[match.end():], _parse_tags(match.group(1))


def _parse_tags(front_matter: str) -> list[str]:
    """Pull the `tags:` value out of YAML front matter, inline list or block list."""
    tags: list[str] = []
    in_block = False
    for line in front_matter.splitlines():
        if in_block:
            item = line.strip()
            if item.startswith("- "):
                tags.append(item[2:].strip().strip("\"'"))
                continue
            in_block = False
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "tags":
            value = value.strip().strip("[]")
            if value:
                tags.extend(part.strip().strip("\"'") for part in value.split(","))
            else:
                in_block = True
    return [tag for tag in tags if tag]


def _split_title(body: str, stem: str) -> tuple[str, str]:
    body = body.strip()
    match = H1_RE.search(body)
    # Only a leading H1 is treated as the title; one further down belongs to the body.
    if match and match.start() == 0:
        return match.group(1).strip(), body[match.end():].strip()
    return stem.replace("-", " ").replace("_", " ").title(), body
