#!/usr/bin/env python3
"""Ingest credit card statement PDFs and export structured CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from statements.categorize import categorize
from statements.parsers.emirates_nbd import EmiratesNBDParser, ParsedStatement


def apply_categories(statement: ParsedStatement) -> None:
    for tx in statement.transactions:
        tx.category = categorize(tx.description)


def write_csv(statements: list[ParsedStatement], output_path: Path) -> None:
    fieldnames = [
        "source_file",
        "statement_period_start",
        "statement_period_end",
        "statement_date",
        "transaction_date",
        "posting_date",
        "description",
        "amount_aed",
        "is_credit",
        "foreign_amount",
        "foreign_currency",
        "category",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for statement in statements:
            for tx in statement.transactions:
                row = tx.to_row()
                row.update(
                    {
                        "source_file": statement.source_file,
                        "statement_period_start": statement.statement_period_start,
                        "statement_period_end": statement.statement_period_end,
                        "statement_date": statement.statement_date,
                    }
                )
                writer.writerow(row)


def summarize(statements: list[ParsedStatement]) -> dict:
    by_category: dict[str, float] = {}
    total_spend = 0.0
    total_credits = 0.0
    tx_count = 0

    for statement in statements:
        total_spend += statement.total_spend
        total_credits += statement.total_credits
        tx_count += len(statement.transactions)
        for tx in statement.transactions:
            if tx.is_credit:
                continue
            by_category[tx.category] = by_category.get(tx.category, 0.0) + tx.amount_aed

    return {
        "statements_processed": len(statements),
        "transactions": tx_count,
        "total_spend_aed": round(total_spend, 2),
        "total_credits_aed": round(total_credits, 2),
        "spend_by_category_aed": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda item: -item[1])},
    }


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


def main() -> int:
    args = parse_args()
    pdfs = collect_pdfs(args.paths)
    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        return 1

    parser = EmiratesNBDParser()
    statements: list[ParsedStatement] = []

    for pdf_path in pdfs:
        statement = parser.parse(pdf_path)
        apply_categories(statement)
        statements.append(statement)
        print(
            f"Parsed {pdf_path.name}: {len(statement.transactions)} transactions "
            f"({statement.statement_period_start} to {statement.statement_period_end})"
        )

    output_path = Path(args.output)
    write_csv(statements, output_path)
    print(f"Wrote {output_path}")

    summary = summarize(statements)
    print(json.dumps(summary, indent=2))

    if args.summary:
        Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {args.summary}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
