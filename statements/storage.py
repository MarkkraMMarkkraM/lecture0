"""Shared CSV, manifest, and merge logic for statement ingestion."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from statements.parsers.emirates_nbd import ParsedStatement, Transaction

CSV_FIELDNAMES = [
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

MANIFEST_VERSION = 1


def period_key(start: str, end: str) -> str:
    return f"{start}|{end}"


def transaction_key(row: dict[str, Any]) -> tuple:
    return (
        row["statement_period_start"],
        row["statement_period_end"],
        row["transaction_date"],
        row["posting_date"],
        row["description"],
        float(row["amount_aed"]),
        _as_bool(row["is_credit"]),
    )


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}


def statement_to_rows(statement: ParsedStatement) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
        rows.append(row)
    return rows


def write_csv(statements: list[ParsedStatement], output_path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for statement in statements:
        rows.extend(statement_to_rows(statement))
    write_csv_rows(rows, output_path)


def write_csv_rows(rows: list[dict[str, Any]], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv_rows(csv_path: Path) -> list[dict[str, Any]]:
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize_rows(rows: list[dict[str, Any]], statements_processed: int | None = None) -> dict:
    by_category: dict[str, float] = {}
    total_spend = 0.0
    total_credits = 0.0

    periods: set[str] = set()
    for row in rows:
        periods.add(period_key(row["statement_period_start"], row["statement_period_end"]))
        amount = float(row["amount_aed"])
        if _as_bool(row["is_credit"]):
            total_credits += amount
        else:
            total_spend += amount
            category = row.get("category") or "uncategorized"
            by_category[category] = by_category.get(category, 0.0) + amount

    return {
        "statements_processed": statements_processed if statements_processed is not None else len(periods),
        "transactions": len(rows),
        "total_spend_aed": round(total_spend, 2),
        "total_credits_aed": round(total_credits, 2),
        "spend_by_category_aed": {
            k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda item: -item[1])
        },
    }


def summarize(statements: list[ParsedStatement]) -> dict:
    rows: list[dict[str, Any]] = []
    for statement in statements:
        rows.extend(statement_to_rows(statement))
    return summarize_rows(rows, statements_processed=len(statements))


def empty_manifest() -> dict[str, Any]:
    return {"version": MANIFEST_VERSION, "files": {}, "statement_periods": {}}


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_manifest()
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("files", {})
    data.setdefault("statement_periods", {})
    return data


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def manifest_entry(
    *,
    file_id: str,
    title: str,
    modified_time: str,
    statement: ParsedStatement,
) -> dict[str, Any]:
    return {
        "title": title,
        "modifiedTime": modified_time,
        "statement_period_start": statement.statement_period_start,
        "statement_period_end": statement.statement_period_end,
        "statement_date": statement.statement_date,
        "transaction_count": len(statement.transactions),
    }


def update_manifest_with_statement(
    manifest: dict[str, Any],
    *,
    file_id: str,
    title: str,
    modified_time: str,
    statement: ParsedStatement,
) -> None:
    manifest["files"][file_id] = manifest_entry(
        file_id=file_id,
        title=title,
        modified_time=modified_time,
        statement=statement,
    )
    key = period_key(statement.statement_period_start, statement.statement_period_end)
    manifest["statement_periods"][key] = file_id


def needs_processing(
    manifest: dict[str, Any],
    *,
    file_id: str,
    modified_time: str,
) -> bool:
    existing = manifest.get("files", {}).get(file_id)
    if not existing:
        return True
    return existing.get("modifiedTime") != modified_time


def merge_statements_into_rows(
    existing_rows: list[dict[str, Any]],
    new_statements: list[ParsedStatement],
) -> list[dict[str, Any]]:
    replaced_periods = {
        period_key(statement.statement_period_start, statement.statement_period_end)
        for statement in new_statements
    }

    kept_rows = [
        row
        for row in existing_rows
        if period_key(row["statement_period_start"], row["statement_period_end"]) not in replaced_periods
    ]

    new_rows: list[dict[str, Any]] = []
    for statement in new_statements:
        new_rows.extend(statement_to_rows(statement))

    merged = kept_rows + new_rows
    merged.sort(
        key=lambda row: (
            row["statement_period_start"],
            row["transaction_date"],
            row["posting_date"],
            row["description"],
        )
    )
    return merged


def rows_from_statements(statements: list[ParsedStatement]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for statement in statements:
        rows.extend(statement_to_rows(statement))
    return rows
