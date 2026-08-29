#!/usr/bin/env python3
"""Build a drive-index JSON from a statement manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build drive-index JSON from statement manifest")
    parser.add_argument("manifest", help="statement_manifest.json path")
    parser.add_argument("-o", "--output", default="drive_index.json", help="Output path")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    index = [
        {"id": file_id, "title": meta["title"], "modifiedTime": meta["modifiedTime"]}
        for file_id, meta in manifest.get("files", {}).items()
    ]
    Path(args.output).write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Wrote {args.output} ({len(index)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
