"""Execute the active saved-evidence notebook and check its declared report profile."""
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import sys
import time


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_default_code(book: dict, profile: dict) -> None:
    code = ["".join(cell["source"]) for cell in book["cells"] if cell["cell_type"] == "code"]
    digest = hashlib.sha256(json.dumps(code, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if digest != profile["code_source_sha256"]:
        raise RuntimeError(
            "main.ipynb code differs from the reviewed native-free defaults. "
            "Restore the default code cells before validation. "
            "Run optional native examples separately after explicitly opting in."
        )


class NoNativeSimulator(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "fish_sim" or fullname.startswith("fish_sim."):
            raise RuntimeError("Default notebook validation must not import the native simulator")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", action="store_true", help="save refreshed outputs to main.ipynb")
    parser.add_argument("--receipt", type=Path, default=Path("validation/main_notebook_validation.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    os.chdir(root)
    sys.path.insert(0, str(root))
    sys.meta_path.insert(0, NoNativeSimulator())
    profile = json.loads((root / "MAIN_NOTEBOOK_PROFILE.json").read_text())
    assert profile["notebook"] == "main.ipynb" and profile["native_steps"] == 0
    assert sha(root / profile["report"]) == profile["report_sha256"], "Report profile changed"
    protected = {}
    for name in profile["protected_manifests"]:
        for relative, digest in json.loads((root / name).read_text())["files"].items():
            assert relative not in protected or protected[relative] == digest
            assert sha(root / relative) == digest, relative
            protected[relative] = digest
    book_path = root / "main.ipynb"
    book = json.loads(book_path.read_text())
    check_default_code(book, profile)  # Reject changed toggles/commands before executing any cell.
    namespace = {"__name__": "__main__"}
    count = 0
    started = time.monotonic()
    for cell in book["cells"]:
        if cell["cell_type"] != "code":
            continue
        count += 1
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile("".join(cell["source"]), f"<main.ipynb cell {count}>", "exec"), namespace)
        cell["execution_count"] = count
        cell["outputs"] = []
        if output.getvalue():
            cell["outputs"].append(dict(output_type="stream", name="stdout", text=output.getvalue().splitlines(True)))
        if name := cell.get("metadata", {}).get("figure"):
            png = root / profile["figure_output"] / (name + ".png")
            cell["outputs"].append(dict(output_type="display_data", data={
                "image/png": base64.b64encode(png.read_bytes()).decode(), "text/plain": [name]}, metadata={}))
    assert count == profile["code_cells"]
    assert namespace["RUN_V6_MODEL"] is False, "Optional model must remain disabled"
    assert not any(n == "fish_sim" or n.startswith("fish_sim.") for n in sys.modules)
    for relative, digest in protected.items():
        assert sha(root / relative) == digest, "Protected input changed: " + relative
    for relative, digest in profile["csv_tables"].items():
        assert sha(root / relative) == digest, "CSV differs from report profile: " + relative
    import numpy as np
    import matplotlib.image as mpimg
    figures = {}
    for name in profile["figure_names"]:
        generated = root / profile["figure_output"] / (name + ".png")
        reference = root / profile["report_figure_reference"] / (name + ".png")
        assert np.array_equal(mpimg.imread(generated), mpimg.imread(reference)), name
        figures[name] = {"sha256": sha(generated), "pixels_identical_to_report": True}
    if args.save:
        book_path.write_text(json.dumps(book, indent=1) + "\n")
    receipt = dict(status="passed", profile=profile["profile"], notebook="main.ipynb",
        notebook_sha256=sha(book_path), report=profile["report"], report_sha256=profile["report_sha256"],
        code_cells=count, csv_tables=len(profile["csv_tables"]), all_csv_bytes_identical=True,
        protected_inputs_unchanged=len(protected), figures=figures, native_steps=0,
        native_imported=False, optional_native_enabled=False, source_root=str(root),
        python=sys.version.split()[0], wall_seconds=time.monotonic()-started)
    receipt_path = args.receipt if args.receipt.is_absolute() else root / args.receipt
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
