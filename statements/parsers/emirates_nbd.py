"""Parser for Emirates NBD credit card e-statement PDFs."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import pdfplumber

DATE_FMT = "%d/%m/%Y"
PERIOD_RE = re.compile(
    r"Statement Period:\s*(\d{2}-[A-Za-z]{3}-\d{2})\s+to\s+(\d{2}-[A-Za-z]{3}-\d{2})"
)
STATEMENT_DATE_RE = re.compile(
    r"Credit Limit Available Credit Limit \(AED\) Statement Date Payment Due Date Minimum Payment Due\s+"
    r"\d[\d,]*\s+[\d,]+\.\d{2}\s+(\d{2}/\d{2}/\d{4})"
)
CARD_RE = re.compile(r"4033 XXXX XXXX (\d{4})")
DATE_TOKEN = r"\d{2}/\d{2}/\d{4}"
AMOUNT = r"(?:\d{1,3}(?:,\d{3})*|\d+)\.\d{2}"
CURRENCIES = ("USD", "EUR", "GBP", "SGD", "AUD", "CAD", "CHF", "JPY", "AED")
CURRENCY_GROUP = "(?:" + "|".join(CURRENCIES) + ")"

TX_RE = re.compile(
    rf"^{DATE_TOKEN}\s+{DATE_TOKEN}\s+(?P<description>.+?)\s+"
    rf"(?P<foreign_amount>{AMOUNT}\s+{CURRENCY_GROUP}\s+(?P<aed_amount>{AMOUNT}))"
    rf"|{DATE_TOKEN}\s+{DATE_TOKEN}\s+(?P<description_simple>.+?)\s+"
    rf"(?P<amount>{AMOUNT}(?:CR)?)$"
)

SKIP_LINE_RE = re.compile(
    r"^(?:\(\d+\s+AED\s+=|\*|Primary Card Number|Transaction Date|Page \d+ of|\.)"
)


@dataclass
class Transaction:
    transaction_date: str
    posting_date: str
    description: str
    amount_aed: float
    is_credit: bool
    foreign_amount: float | None = None
    foreign_currency: str | None = None
    category: str = "uncategorized"

    def to_row(self) -> dict[str, str | float | bool]:
        return {
            "transaction_date": self.transaction_date,
            "posting_date": self.posting_date,
            "description": self.description,
            "amount_aed": self.amount_aed,
            "is_credit": self.is_credit,
            "foreign_amount": self.foreign_amount or "",
            "foreign_currency": self.foreign_currency or "",
            "category": self.category,
        }


@dataclass
class ParsedStatement:
    source_file: str
    bank: str = "Emirates NBD"
    card_last_four: str = ""
    card_type: str = ""
    statement_period_start: str = ""
    statement_period_end: str = ""
    statement_date: str = ""
    transactions: list[Transaction] = field(default_factory=list)

    @property
    def total_spend(self) -> float:
        return sum(t.amount_aed for t in self.transactions if not t.is_credit)

    @property
    def total_credits(self) -> float:
        return sum(t.amount_aed for t in self.transactions if t.is_credit)


def _parse_period_date(value: str) -> str:
    return datetime.strptime(value, "%d-%b-%y").strftime(DATE_FMT)


def _parse_amount(value: str) -> tuple[float, bool]:
    is_credit = value.endswith("CR")
    cleaned = value[:-2] if is_credit else value
    return float(cleaned.replace(",", "")), is_credit


def _extract_text(source: BinaryIO | Path) -> str:
    if isinstance(source, Path):
        pdf = pdfplumber.open(source)
    else:
        pdf = pdfplumber.open(source)
    with pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


class EmiratesNBDParser:
    """Extract transactions from Emirates NBD credit card PDF statements."""

    def parse(self, source: BinaryIO | Path, source_name: str = "") -> ParsedStatement:
        if isinstance(source, Path):
            source_name = source_name or source.name
            text = _extract_text(source)
        else:
            source_name = source_name or "statement.pdf"
            text = _extract_text(source)

        result = ParsedStatement(source_file=source_name)
        card_match = CARD_RE.search(text)
        if card_match:
            result.card_last_four = card_match.group(1)

        if "Etihad Guest Visa Elevate" in text:
            result.card_type = "Etihad Guest Visa Elevate"

        period_match = PERIOD_RE.search(text)
        if period_match:
            result.statement_period_start = _parse_period_date(period_match.group(1))
            result.statement_period_end = _parse_period_date(period_match.group(2))

        date_match = STATEMENT_DATE_RE.search(text)
        if date_match:
            result.statement_date = date_match.group(1)

        in_transactions = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("Transaction Date Posting Date Description Amount"):
                in_transactions = True
                continue

            if in_transactions and line.startswith("STATEMENT SUMMARY"):
                break

            if not in_transactions:
                continue

            if SKIP_LINE_RE.match(line):
                continue

            if "MARK STUART MATTHEWS:" in line or line.startswith("Primary Card"):
                continue

            tx = self._parse_transaction_line(line)
            if tx:
                result.transactions.append(tx)

        return result

    def _parse_transaction_line(self, line: str) -> Transaction | None:
        match = TX_RE.match(line)
        if not match:
            return None

        if match.group("foreign_amount"):
            dates = re.match(rf"^({DATE_TOKEN})\s+({DATE_TOKEN})\s+", line)
            if not dates:
                return None
            amount, _ = _parse_amount(match.group("aed_amount"))
            foreign_amount, _ = _parse_amount(match.group("foreign_amount").split()[0])
            foreign_currency = match.group("foreign_amount").split()[1]
            return Transaction(
                transaction_date=dates.group(1),
                posting_date=dates.group(2),
                description=match.group("description").strip(),
                amount_aed=amount,
                is_credit=False,
                foreign_amount=foreign_amount,
                foreign_currency=foreign_currency,
            )

        description = match.group("description_simple").strip()
        amount, is_credit = _parse_amount(match.group("amount"))
        dates = re.match(rf"^({DATE_TOKEN})\s+({DATE_TOKEN})\s+", line)
        if not dates:
            return None

        return Transaction(
            transaction_date=dates.group(1),
            posting_date=dates.group(2),
            description=description,
            amount_aed=amount,
            is_credit=is_credit,
        )

    def parse_bytes(self, pdf_bytes: bytes, source_name: str = "statement.pdf") -> ParsedStatement:
        return self.parse(io.BytesIO(pdf_bytes), source_name=source_name)
