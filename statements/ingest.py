#!/usr/bin/env python3
"""Ingest credit card statement PDFs and export structured CSV."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from statements.categorize import categorize
from statements.parsers.emirates_nbd import EmiratesNBDParser, ParsedStatement
from statements.storage import (
    load_manifest,
    summarize,
    update_manifest_with_statement,
    write_csv,
    write_manifest,
)


def apply_categories(statement: ParsedStatement) -> None:
    for tx in statement.transactions:
        tx.category = categorize(tx.description)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse Emirates NBD credit card statement PDFs")
    parser.add_argument(
        "paths",
        nargs="+",
        help="PDF file(s) or folder(s) containing PDF statements",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="transactions.csv",
        help="Output CSV path (default: transactions.csv)",
    )
    parser.add_argument(
        "--summary",
        help="Optional JSON summary output path",
    )
    parser.add_argument(
        "--manifest",
        help="Optional manifest output path (requires --drive-index)",
    )
    parser.add_argument(
        "--drive-index",
        help="JSON listing Drive PDFs: [{id, title, modifiedTime}, ...]",
    )
    return parser.parse_args()


def collect_pdfs(paths: list[str]) -> list[Path]:
    pdfs: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            pdfs.extend(sorted(path.glob("*.pdf")))
            pdfs.extend(sorted(path.glob("*.PDF")))
        elif path.is_file():
            pdfs.append(path)
        else:
            raise FileNotFoundError(f"Path not found: {path}")
    return pdfs


def load_drive_index_by_id(path: Path) -> dict[str, dict[str, str]]:
    items = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in items}


def main() -> int:
    args = parse_args()
    pdfs = collect_pdfs(args.paths)
    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        return 1

    drive_by_id: dict[str, dict[str, str]] = {}
    if args.drive_index:
        drive_by_id = load_drive_index_by_id(Path(args.drive_index))
    elif args.manifest:
        print("--manifest requires --drive-index", file=sys.stderr)
        return 1

    parser = EmiratesNBDParser()
    statements: list[ParsedStatement] = []
    manifest = load_manifest(Path(args.manifest)) if args.manifest else None

    for pdf_path in pdfs:
        statement = parser.parse(pdf_path)
        apply_categories(statement)
        statements.append(statement)
        print(
            f"Parsed {pdf_path.name}: {len(statement.transactions)} transactions "
            f"({statement.statement_period_start} to {statement.statement_period_end})"
        )
        if manifest is not None:
            meta = drive_by_id.get(pdf_path.stem)
            if not meta:
                print(f"Warning: no Drive metadata for {pdf_path.name}, skipping manifest entry", file=sys.stderr)
                continue
            update_manifest_with_statement(
                manifest,
                file_id=meta["id"],
                title=meta["title"],
                modified_time=meta["modifiedTime"],
                statement=statement,
            )

    output_path = Path(args.output)
    write_csv(statements, output_path)
    print(f"Wrote {output_path}")

    summary = summarize(statements)
    print(json.dumps(summary, indent=2))

    if args.summary:
        Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {args.summary}")

    if manifest is not None and args.manifest:
        write_manifest(Path(args.manifest), manifest)
        print(f"Wrote {args.manifest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
