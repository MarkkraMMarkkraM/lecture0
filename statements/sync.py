#!/usr/bin/env python3
"""Incremental sync: merge new/changed statement PDFs into an existing CSV."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from statements.categorize import categorize
from statements.parsers.emirates_nbd import EmiratesNBDParser, ParsedStatement
from statements.drive_io import (
    DRIVE_FOLDER_ID,
    DriveCredentialsMissing,
    upload_from_disk,
)
from statements.storage import (
    load_manifest,
    merge_statements_into_rows,
    needs_processing,
    read_csv_rows,
    summarize_rows,
    update_manifest_with_statement,
    write_csv_rows,
    write_manifest,
)


def apply_categories(statement: ParsedStatement) -> None:
    for tx in statement.transactions:
        tx.category = categorize(tx.description)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Incrementally sync Emirates NBD statement PDFs into transactions.csv"
    )
    parser.add_argument(
        "--csv",
        default="transactions.csv",
        help="Existing transactions CSV (created or updated in place)",
    )
    parser.add_argument(
        "--manifest",
        default="statement_manifest.json",
        help="Manifest tracking processed Drive files",
    )
    parser.add_argument(
        "--summary",
        help="Optional JSON summary output path",
    )
    parser.add_argument(
        "--drive-index",
        help="JSON file listing Drive PDFs: [{id, title, modifiedTime}, ...]",
    )
    parser.add_argument(
        "pdfs",
        nargs="*",
        help="PDF files to consider (must include --file-id and --modified-time metadata)",
    )
    parser.add_argument(
        "--pdf-folder",
        help="Local folder of downloaded PDFs (uses filename as title; file-id from drive-index)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be processed without writing outputs",
    )
    parser.add_argument(
        "--upload-drive",
        action="store_true",
        help=(
            "After writing local CSV/manifest, upload from disk via Drive API "
            "(requires GOOGLE_DRIVE_TOKEN or ADC). Never uses Drive MCP inline content."
        ),
    )
    parser.add_argument(
        "--drive-folder-id",
        default=DRIVE_FOLDER_ID,
        help="Drive parent folder id for from-disk upload",
    )
    parser.add_argument(
        "--drive-csv-file-id",
        help="Existing Drive transactions.csv file id to replace (optional)",
    )
    return parser.parse_args()


def load_drive_index(path: Path | None) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    if not path:
        return {}, {}
    items = json.loads(path.read_text(encoding="utf-8"))
    by_title: dict[str, dict[str, str]] = {}
    by_id: dict[str, dict[str, str]] = {}
    for item in items:
        by_title[item["title"]] = item
        by_id[item["id"]] = item
    return by_title, by_id


def lookup_drive_meta(
    pdf_path: Path,
    by_title: dict[str, dict[str, str]],
    by_id: dict[str, dict[str, str]],
) -> dict[str, str]:
    meta = by_title.get(pdf_path.name) or by_id.get(pdf_path.stem)
    if not meta:
        raise ValueError(
            f"No Drive metadata for {pdf_path.name}. "
            "Provide --drive-index or process via ingest for local-only files."
        )
    return meta


def collect_pdf_jobs(
    pdf_paths: list[Path],
    by_title: dict[str, dict[str, str]],
    by_id: dict[str, dict[str, str]],
) -> list[tuple[Path, str, str, str]]:
    jobs: list[tuple[Path, str, str, str]] = []
    for pdf_path in pdf_paths:
        meta = lookup_drive_meta(pdf_path, by_title, by_id)
        jobs.append((pdf_path, meta["id"], meta["title"], meta["modifiedTime"]))
    return jobs


def collect_folder_jobs(
    folder: Path,
    by_title: dict[str, dict[str, str]],
    by_id: dict[str, dict[str, str]],
) -> list[tuple[Path, str, str, str]]:
    pdfs = sorted(folder.glob("*.pdf")) + sorted(folder.glob("*.PDF"))
    return collect_pdf_jobs(pdfs, by_title, by_id)


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    by_title, by_id = load_drive_index(Path(args.drive_index) if args.drive_index else None)

    jobs: list[tuple[Path, str, str, str]] = []
    if args.pdf_folder:
        jobs.extend(collect_folder_jobs(Path(args.pdf_folder), by_title, by_id))
    elif args.pdfs:
        jobs.extend(collect_pdf_jobs([Path(p) for p in args.pdfs], by_title, by_id))

    if not jobs:
        print("No PDFs provided. Use --pdf-folder or pass PDF paths with --drive-index.", file=sys.stderr)
        return 1

    parser = EmiratesNBDParser()
    to_process: list[tuple[Path, str, str, str]] = []
    skipped = 0

    for pdf_path, file_id, title, modified_time in jobs:
        if needs_processing(manifest, file_id=file_id, modified_time=modified_time):
            to_process.append((pdf_path, file_id, title, modified_time))
        else:
            skipped += 1
            print(f"Skip (unchanged): {title}")

    if not to_process:
        print(f"Nothing to do. {skipped} file(s) already up to date.")
        return 0

    new_statements: list[ParsedStatement] = []
    for pdf_path, file_id, title, modified_time in to_process:
        statement = parser.parse(pdf_path, source_name=title)
        apply_categories(statement)
        new_statements.append(statement)
        update_manifest_with_statement(
            manifest,
            file_id=file_id,
            title=title,
            modified_time=modified_time,
            statement=statement,
        )
        print(
            f"Parsed {title}: {len(statement.transactions)} transactions "
            f"({statement.statement_period_start} to {statement.statement_period_end})"
        )

    existing_rows = read_csv_rows(csv_path)
    merged_rows = merge_statements_into_rows(existing_rows, new_statements)
    summary = summarize_rows(merged_rows)

    print(json.dumps({"processed": len(to_process), "skipped": skipped, **summary}, indent=2))

    if args.dry_run:
        print("Dry run — no files written.")
        return 0

    write_csv_rows(merged_rows, csv_path)
    write_manifest(manifest_path, manifest)
    print(f"Wrote {csv_path} ({len(merged_rows)} transactions)")
    print(f"Wrote {manifest_path}")

    if args.summary:
        Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {args.summary}")

    if args.upload_drive:
        try:
            result = upload_from_disk(
                csv_path,
                parent_id=args.drive_folder_id,
                title=csv_path.name,
                file_id=args.drive_csv_file_id,
            )
            print(
                f"Drive {result.get('action')}: {result.get('name')} "
                f"id={result.get('id')} size={result.get('size')}"
            )
            if args.summary:
                summary_result = upload_from_disk(
                    Path(args.summary),
                    parent_id=args.drive_folder_id,
                    title=Path(args.summary).name,
                    mime_type="application/json",
                )
                print(
                    f"Drive {summary_result.get('action')}: {summary_result.get('name')} "
                    f"id={summary_result.get('id')}"
                )
            manifest_result = upload_from_disk(
                manifest_path,
                parent_id=args.drive_folder_id,
                title=manifest_path.name,
                mime_type="application/json",
                file_id="16HGkaK6Jdr2r3a-_yhuyW_gIp3Scfwk4",
            )
            print(
                f"Drive {manifest_result.get('action')}: {manifest_result.get('name')} "
                f"id={manifest_result.get('id')}"
            )
        except DriveCredentialsMissing as exc:
            print(f"Drive upload skipped (no credentials): {exc}", file=sys.stderr)
            print(
                "Local files are ready. Upload from disk via Drive web UI file picker "
                "or retry with GOOGLE_DRIVE_TOKEN / ADC.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
