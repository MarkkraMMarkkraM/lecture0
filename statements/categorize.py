"""Rule-based merchant categorization (no AI tokens)."""

from __future__ import annotations

import re

RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"AMAZON|WAITROSE|CARREFOUR|GROCERY", re.I), "groceries"),
    (re.compile(r"CAREEM FOOD|RESTAUR|CANTEEN|CAFE|COFFEE|PIZZA|BURGER|FIVE GUYS|DIN TAI|PHO|WOK|STEAK|BISTRO|BAR |HOTEL|INN ", re.I), "dining"),
    (re.compile(r"OPENAI|CHATGPT|XAI|GROK|GOOGLE ONE|X CORP|CURSOR|NOMADESIM", re.I), "subscriptions"),
    (re.compile(r"APPLE\.COM|ITUNES|AMAZON PRIME", re.I), "subscriptions"),
    (re.compile(r"ADNOC|ENOC|TAXI|CAREEM RIDE|PARKING|PARKONIC|TRANSPORT", re.I), "transport"),
    (re.compile(r"NORD ANGLIA|SMART DUBAI", re.I), "education"),
    (re.compile(r"INSURANCE|SUKOON", re.I), "insurance"),
    (re.compile(r"PAYMENT RECEIVED|TRANSFER PAYMENT", re.I), "payment"),
    (re.compile(r"FEE|VAT ON", re.I), "fees"),
    (re.compile(r"LENSKART|BRANDS FOR LESS|MUMUSO|BOOTS|PHARM", re.I), "shopping"),
    (re.compile(r"VOX CINEMA|REEL ENTERTAINMENT|ENTERTAIN", re.I), "entertainment"),
    (re.compile(r"DISTRIBUTION|COOLING|PAL TAMOUH", re.I), "utilities"),
    (re.compile(r"THE CLUB", re.I), "membership"),
]


def categorize(description: str) -> str:
    for pattern, label in RULES:
        if pattern.search(description):
            return label
    return "other"
