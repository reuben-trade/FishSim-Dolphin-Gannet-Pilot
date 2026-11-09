"""Add saved-replay help to main.ipynb without changing its reviewed code.

Run after the pinned current-paper generator. Only the introductory Markdown
source array is rewritten; code, outputs, IDs and metadata retain their bytes.
No notebook kernel, model import or simulation is started.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- fishsim-recorded-replays:start -->"
END = "<!-- fishsim-recorded-replays:end -->"
SECTION = f"""{START}
## Watch recorded 3D runs

Open a **Terminal in this repository's root folder** and run:

```bash
python tools/watch_replays.py
```

The viewer plays saved run data, including recorded attacks and captures. It
does not import the native simulator or execute a new simulation. See the
[visualisation guide](docs/VISUALISATION.md) and [README](README.md) for the
available recordings and viewing options.
{END}"""


def code_digest(book):
    code = ["".join(c["source"]) for c in book["cells"] if c["cell_type"] == "code"]
    return hashlib.sha256(json.dumps(code, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def updated_intro(text):
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError("Replay-help markers are incomplete or duplicated")
    if START not in text:
        return text.rstrip() + "\n\n" + SECTION + "\n"
    start = text.index(START)
    stop = text.index(END, start) + len(END)
    return text[:start] + SECTION + text[stop:]


def replace_source_array(raw, previous, replacement):
    """Replace this one JSON value; leave every other stored byte untouched."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r'"source"\s*:\s*', raw):
        try:
            value, stop = decoder.raw_decode(raw, match.end())
        except json.JSONDecodeError:
            continue
        if value != previous:
            continue
        line_start = raw.rfind("\n", 0, match.start()) + 1
        prefix = raw[line_start:match.start()]
        if prefix.strip():
            raise ValueError("Expected the current notebook's indented source layout")
        encoded = json.dumps(replacement, ensure_ascii=False, indent=1)
        encoded = encoded.replace("\n", "\n" + prefix)
        return raw[:match.end()] + encoded + raw[stop:]
    raise ValueError("Could not locate the introductory Markdown source array")


def update(notebook, profile, *, check=False):
    notebook = Path(notebook)
    raw = notebook.read_text(encoding="utf-8")
    book = json.loads(raw)
    if len(book["cells"]) != 21 or sum(c["cell_type"] == "code" for c in book["cells"]) != 10:
        raise ValueError("Expected the current 21-cell, 10-code-cell notebook; review its profile first")
    intro = book["cells"][0]
    if intro["cell_type"] != "markdown" or not isinstance(intro["source"], list):
        raise ValueError("Expected an introductory Markdown cell with a source array")
    digest = code_digest(book)
    if digest != profile["code_source_sha256"]:
        raise ValueError("Notebook code differs from the reviewed profile; this tool only changes viewing help")
    replacement = updated_intro("".join(intro["source"])).splitlines(keepends=True)
    changed = replacement != intro["source"]
    if changed:
        if check:
            raise ValueError("Recorded-replay help is missing or outdated; run this tool without --check")
        updated = replace_source_array(raw, intro["source"], replacement)
        after = json.loads(updated)
        expected_intro = dict(intro, source=replacement)
        if after["cells"][0] != expected_intro or after["cells"][1:] != book["cells"][1:]:
            raise AssertionError("A notebook field outside the introductory Markdown changed")
        if {k:v for k,v in after.items() if k != "cells"} != {k:v for k,v in book.items() if k != "cells"}:
            raise AssertionError("Notebook metadata changed")
        if code_digest(after) != digest:
            raise AssertionError("Reviewed code changed")
        temporary = notebook.with_name("." + notebook.name + ".viewer-help.tmp")
        temporary.write_text(updated, encoding="utf-8")
        temporary.replace(notebook)
    return dict(status="passed", changed=changed, notebook=str(notebook),
                total_cells=21, code_cells=10, code_source_sha256=digest,
                native_simulation_steps=0, notebook_kernel_started=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path, default=ROOT/"main.ipynb")
    parser.add_argument("--check", action="store_true", help="Check the help without writing anything")
    args = parser.parse_args()
    profile = json.loads((ROOT/"MAIN_NOTEBOOK_PROFILE.json").read_text())
    print(json.dumps(update(args.notebook, profile, check=args.check), indent=2))


if __name__ == "__main__":
    main()
