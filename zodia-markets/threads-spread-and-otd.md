# Zodia Markets — Threads pulled together

**Status:** Working synthesis. Not a decision. Companion to `onchain-credit-desk.md`.
**Date:** 7 September 2026
**What this file is:** the argument that emerged after the first deck note — funding-cost advantage, the $200m / $9m ceiling, and originate-to-distribute as the third line.

---

## The one-line thesis

Zodia Markets should be a **credit-portal desk with its own liquidation engine**, funded at **SOFR + 80**, originating into onchain markets and **distributing** the paper — not a vault curator, not a prime broker, not a hold-to-maturity lender.

37C owns the client wrapper. The desk owns the engine and the warehouse.

---

## Thread 1 — Funding cost is the unfair advantage

Wintermute (and peers) fund unsecured onchain at ~8.5–9.25% (Wildcat USDC ~8.5% live; the 9.25% figure is the earlier fixed-APR print used in the Armitage launch write-up). Zodia’s internal funding is **SOFR + 80**.

At SOFR ~3.66% (early September 2026):

- All-in funding ≈ **4.46–4.50%**
- Onchain unsecured ask ≈ **9.25%**
- Gross spread ≈ **4.75 points**

On **$200 million** deployed and fully utilised:

- 4.5% × $200m = **$9.0m**
- 4.75% × $200m = **$9.5m**

That is the **ceiling**, not the base case. Put it on the slide as “what the spread is worth *if* the engine exists.”

### Where the spread actually lives

| Book | Observed net | vs SOFR+80 | Treat as |
|---|---|---|---
| Aave V3 USDC supply | ~2.1% | negative | Do not touch as a carry book |
| Morpho Steakhouse Prime | ~4.2–4.4% | 0–40 bps | Parking, not the product |
| Wintermute Select / higher Morpho | ~4.9–5.5% | 40–100 bps | Better, still thin |
| Maple syrupUSDC | ~5.0% | ~50 bps | Tokenised private credit — existing muscle |
| Self-referencing structures (Wildcat → wrap → Morpho collateral) | ~9.2% borrow / 4.5% fund | **~450–475 bps** | The $9m line |

Vanilla vault deposits do not pay for a desk. The four-and-a-half points only appear when the collateral is **self-referencing** — a credit claim the desk itself can liquidate or recover.

---

## Thread 2 — The engine is the product

The load-bearing sentence from the first note still holds:

> The desk is only as good as the liquidation engine underneath it. In a depeg or oracle failure, curators who liquidate their own collateral clear in minutes; everyone else queues, and the queue is where the losses live.

Without the engine:
- you cannot safely warehouse self-referencing collateral
- buyers will not pay a premium for your paper
- you are back to 30–100 bps — a million or two on $200m, not nine

With the engine:
- you capture the funding spread on whatever you *hold*
- you earn the liquidation incentive (LIF ~5% at 86% LLTV, capped 15%) when positions break
- you can run a distressed-claims book: buy the claim at the oracle’s discounted price, recover off-chain, keep the gap

**Build order does not change:** trading function and liquidation capability first; vault tickets second. RFS “no effective limits” stays the internal cautionary tale and stays off client slides.

---

## Thread 3 — Originate-to-distribute (the offtake)

This is the third revenue stream and the capital-efficiency move.

**Model.** Underwrite the loan. Warehouse it briefly on the desk. Sell it into:
- a curated Morpho / private-credit vault
- a tokenised credit wrapper (Maple-style syrup, or a buyer’s own fund)
- an institutional offtaker who wants the yield but not the origination work

The balance sheet is a **warehouse**, not a permanent holder. Capital turns over.

**Fee stack.**
1. Origination fee — paid at close.
2. Distribution / placement margin — bid-offer between warehouse carry and buyer yield.
3. **Servicing strip** — keep collecting, monitoring collateral, running the liquidation playbook after the loan leaves the book. Recurring, low-capital, compounds with stock of paper in the market.

**Why this is the right perimeter.** You are not pooling client money into a vault you curate. You are selling a credit *asset* to a buyer who does their own DD. Buyer takes credit risk. Desk takes fees. That is **markets activity**, not asset management — which is the point of keeping own capital in a non-regulated Cayman shell and clients only through a separately authorised wrapper (the prime desk / 37C).

**What buyers will actually pay for.** Underwriting they trust *plus* evidence you can recover in stress. The engine is what makes the paper distributable at a premium. Originate all day without it and you are selling par credit into a market that already has Maple, Steakhouse, and Gauntlet.

---

## How the three lines stack

| Line | What you earn | Capital intensity | Condition |
|---|---|---|---
| 1. Funding spread | SOFR+80 in, onchain borrow / self-ref structure out. Ceiling ~4.5–4.75 pts | High while held | Engine + allowlisted venues |
| 2. Liquidation / distressed claims | LIF bonus + recovery gap on seized or discounted claims | Medium, episodic | Engine. This *is* the engine P&L |
| 3. OTD + servicing strip | Origination + placement + ongoing servicing | Low once distributed | Engine (so paper clears) + buyer roster |

Slide line for the committee:

> Curation fees are a rounding error. A credit desk with its own engine earns the spread while it holds, the liquidation premium when it breaks, and the servicing strip after it leaves. The $9m on $200m is the hold-book ceiling. OTD is how that book does not have to stay $200m of *our* capital.

---

## 37C vs the desk (do not blur)

- **37C / prime:** custody, margin, reporting, client relationship. Where the name lives.
- **Zodia Markets desk:** origination, warehouse, liquidation, distribution. Where the money is made.
- Clients route *through* prime into the engine — or 37C competes without liquidation capability. Either framing is fine internally; do not put both businesses on one balance sheet.

Same split as the first note: own capital in the non-regulated entity (Cayman template — Corto-style, Terms disclaim CIS/AIF). Third-party money only through an authorised wrapper. FCA crypto lending/borrowing as dealing or arranging from October 2027. Named curator + fee flows fails the DeFi carve-out. Pooled client returns → CIS / AIFM territory.

---

## Entity reminder (Cayman vs DMCC)

Cayman remains the cleaner *proprietary* shell: institutional recognition for offshore credit, zero tax, no VASP if you stay off client money and disclaim the fund perimeter.

DMCC / VARA is the path if the desk ever takes external clients or needs UAE banking substance. Prop trading in DMCC still wants a VARA NOC; full VASP if client funds appear. 37C is being built in the UAE for a reason — that is the regulated home. The sandbox stays offshore until the first external dollar.

---

## What has to be true before the $9m sentence is used in a room

1. Named first-line owner. Hard limits, throttles, overnight safeguards.
2. Liquidation playbook written — build or explicitly outsource. No “we’ll figure it out in live markets.”
3. ERC-4626 + market **allowlist**. No permissionless browsing.
4. Same limit grammar as Circle / Ripple / Cumberland, applied to vaults and to names.
5. Offtaker list: who buys the paper on day one (vault curator, tokenised credit wrapper, internal 37C client, external credit fund).
6. 90-day test still stands: ring-fenced entity, capped notional, one stable, two venues, kill conditions (depeg, curator drift, oracle failure, withdrawal queue). Gate: keep / revise / kill.
7. Do not quote $9m as run-rate until utilisation, warehouse duration, and offtake haircut are observed — it is a fully-deployed, fully-utilised, self-ref-book *ceiling*.

---

## Open questions to resolve before the next draft of the deck

- Is the $200m a warehouse cap, a hold-to-maturity cap, or an originate-and-roll capacity? The P&L story changes with each.
- Who is the first offtaker — Morpho curator, Maple-style wrapper, or a named SC / 37C client?
- Do we build the liquidation engine or contract it? “Wintermute-style” is a capability statement, not a build spec.
- Servicing strip: legally a markets fee or a regulated credit-servicing activity in the wrapper jurisdiction?
- How much of the 4.75 pts survives after Fireblocks / PMS ops cost, credit staff, and unused warehouse buffer?

---

## File map

- `onchain-credit-desk.md` — original three-slide note + ecosystem ladder + Wintermute/Wildcat proof.
- `threads-spread-and-otd.md` — this file. Spread arithmetic, engine-as-condition, OTD / offtake, stacked P&L.
