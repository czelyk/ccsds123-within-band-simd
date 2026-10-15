#!/usr/bin/env python3
"""Check the curated public snapshot without compiling, importing or downloading."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    failures = []
    manifest = json.loads((ROOT / "FILE_MANIFEST.json").read_text())
    files = manifest["files"]
    for name, expected in files.items():
        path = ROOT / name
        if not path.is_file():
            failures.append("Missing: " + name)
        elif sha(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
            failures.append("Changed: " + name)

    source_manifest = json.loads((ROOT / "research/ccsds123-revision/original-source-manifest.json").read_text())
    copies = ("iac2027-vector-compression-kit/src", "ccsds123-independent-reassessment/src/reference_kernels", "ccsds123-revision/src/reference_kernels")
    for copy in copies:
        for name, expected in source_manifest.items():
            path = ROOT / "research" / copy / name
            if not path.is_file() or sha(path) != expected:
                failures.append("Original reference source mismatch: " + str(path.relative_to(ROOT)))

    for name in files:
        path = ROOT / name
        if not path.is_file():
            continue
        try:
            if path.suffix == ".json":
                json.loads(path.read_text())
            elif path.suffix == ".jsonl":
                for line in path.read_text().splitlines():
                    if line.strip():
                        json.loads(line)
            elif path.suffix == ".py" and "prior-source" not in path.parts:
                ast.parse(path.read_text(), filename=name)
        except (ValueError, SyntaxError) as error:
            failures.append("Parse failure: " + name + ": " + str(error))

    primary_docs = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
    primary_docs += list((ROOT / "research/ccsds123-final-feasibility").glob("*.md"))
    for path in primary_docs:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            if target and not (path.parent / target).exists():
                failures.append("Missing documentation target: " + str(path.relative_to(ROOT)) + " -> " + target)

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"PASS: {len(files)} public files verified; {len(source_manifest)} original reference files match in all {len(copies)} copies.")
    print("PASS: active Python/JSON records and primary documentation links checked. No benchmark or physical test was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
