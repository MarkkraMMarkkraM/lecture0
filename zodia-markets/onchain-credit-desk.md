# Zodia Markets — Onchain Credit Desk

**Status:** Working draft — proprietary capital, non-regulated sandbox. Not a decision.
**Audience:** Internal strategy / risk committee. Client-safe version to follow.
**Date:** 7 September 2026

---

## Slide 1 — Why a desk now

**Connect the credit book to onchain credit portals.**

Lending has split into two layers: isolated markets underneath, curator vaults on top. That is the institutional rail.

- **Morpho:** open credit network; markets + third-party vaults. Deposits ~$14bn (Sep 2026). Vaults are where institutions actually sit.
- **Aave:** still the depth pool for blue-chip stables / ETH. V4 hub-and-spoke converging on isolated markets.
- **Wintermute / Armitage (the hook):** launched Morpho USDC Prime / Select in May; 2 Sep expanded into USDT vaults, zero fees. Edge is their own liquidation engine — they can take collateral types other curators will not.

The product is not “list on Aave.” It is a **permissioned front + credit process** that allocates into curated vaults, with our liquidation / risk overlay.

**The load-bearing point:** the desk is only as good as the liquidation engine underneath it. In a depeg or oracle failure, curators who liquidate their own collateral clear in minutes; everyone else queues, and the queue is where the losses live.

---

## Slide 2 — Desk design (Zodia Markets)

**A credit-portal desk, not another FX ramp. Markets activity, not prime brokerage.**

| | From Omi / internal
|---|---
| **Mandate** | Plug the existing credit / liquidity book into Aave, Morpho (and peers) as *portals* — supply, borrow, vault deposit, curated strategies.
| **Right to win** | Permissioned markets; banking and custody relationships already there; ring-fenced non-regulated test entity if needed.
| **Product stack named in the room (2 Sep)** | Collateralised lending · liquidity · DeFi / DEX lending · tokenised securities · funding-rate arb · **liquidation services**.
| **Adjacent live colour** | Treasury programme approved (3 Jul). BTC-backed lending path for named names (limit / LTV still in review). Cumberland board-authority proposal is a live path.
| **Do not mix** | Regulated credit process stays separate from open DeFi execution. Aura and the independent Web3 path stay on their own rails.

**31 Aug colour that belongs here:** credit expertise is thin; Ethereum-based lending / stables / custody / staking were named as the white space.

**Funding cost:** SOFR + 80 (~4.5% all-in at SOFR 3.66%, Sep 2026).

**Deployable spreads (observed, Sep 2026):**

| Venue | Net APY | Spread vs SOFR+80 |
|---|---|---
| Aave V3 USDC | ~2.1% | negative — do not touch |
| Morpho Steakhouse Prime | ~4.2–4.4% | ~30–40 bps |
| Wintermute Select | ~4.9–5.5% | ~40–100 bps |
| Steakhouse High Yield | ~5.5–6.2% | ~100–170 bps |
| Maple syrupUSDC | ~5.0% | ~50 bps (tokenised private credit — existing muscle) |

The three-point spreads only appear in self-referencing structures (Wildcat / v-wmtUSDC loops) — and those are exactly the ones a borderline desk cannot clear today.

**37C interplay:** 37C is building the prime-brokerage wrapper (custody, margin, reporting) for SC Ventures clients. Zodia Markets becomes the engine those clients route through — or competes on the liquidation capability 37C will not have. Either way, the prime desk is where the relationship lives; the credit desk is where the money is made.

---

## Slide 3 — What has to exist before the first vault ticket

**Build order: trading function first, vaults second.**

**Control**
- Named first-line owner. Second line does not run the book.
- Hard limits, throttles, overnight safeguards. (RFS “no effective limits” is the internal cautionary tale — keep that off a client slide.)
- LTV / liquidation playbook. Either build a Wintermute-style engine or explicitly outsource it.
- Wallet lifecycle + inbound/outbound screening *before* protocol addresses go live.
- Fireblocks / PMS as the settlement rail, not a side wallet.

**Credit**
- Hire or borrow the credit skill the 31 Aug note flagged as missing.
- Curator DD: Gauntlet, Steakhouse, Armitage, Galaxy, etc.
- Protocol risk: oracle, isolation, curator mandate, fees, pause rights.
- Same limit grammar as Circle / Ripple / Cumberland — applied to vaults, not just names.
- ERC-4626 + market **allowlist**. No permissionless browsing.

**Entity & perimeter**
- Non-regulated entity for proprietary capital (Cayman template, as Wintermute’s Corto Industries does — zero fees, no VASP registration, Terms disclaim CIS/AIF status). Basel 1,250% risk weight on direct crypto vs ~400% on a venture stake.
- The moment third-party money enters, the perimeter moves: FCA regime from Oct 2027 treats crypto lending/borrowing as dealing or arranging; a named curator with fee flows fails the DeFi carve-out. Pooled client returns → collective investment scheme / AIFM territory.
- Clean split: own capital in the non-regulated entity; clients only through a separately authorised wrapper (the prime desk). Never blur the two.

**90-day test**
- Ring-fenced entity, capped notional.
- One stablecoin, two venues: Morpho blue-chip vault + Aave supply-only.
- Kill conditions written down: depeg, curator drift, oracle failure, withdrawal queue.
- No client money until ops/finance capacity and the formal risk-limit path exist.
- Gate: keep / revise / kill after 90 days of observed liquidity.

---

## Appendix — Ecosystem map (risk ladder)

1. **TradFi collateralised lending** — physically delivered BTC/ETH, OTC, documented. Existing book. Lowest risk, lowest yield.
2. **Tokenised private credit** — Maple, Centrifuge, Goldfinch, Clearpool. Real borrowers, off-chain underwriting. ~9–15% yields.
3. **Permissionless overcollateralised lending** — Aave, Morpho. Depth pool. Raw material everything else builds on.
4. **Curated vaults** — Steakhouse, Gauntlet, Armitage. Someone else does the credit work. 3–7% yields. Trap if you just deposit.
5. **Unsecured on-chain credit** — Wildcat. No collateral. Wintermute borrows here at ~8.5–9.25%, wraps as v-wmtUSDC, posts in Select. Your deposit funds their leverage.

**Play:** own the middle. Fund into rungs 3 and 4 on our own terms, with our own liquidation capability. Let 37C handle the prime-brokerage wrapper.

---

## Appendix — Wintermute / Wildcat structure (the proof)

- Wintermute borrows unsecured on Wildcat (~8.5% USDC, ~8.75% USDT as of Sep 2026; ~$75m outstanding).
- Lenders receive a rebasing debt token (wmtUSDC). It is *their* asset — Wintermute cannot burn it.
- Token wraps into v-wmtUSDC (ERC-4626 shell). Anyone holding can post it as collateral in Armitage Select.
- Select accepts it at high LLTV (~91.5%, inferred from tier; blue-chip markets at 86%).
- Wildcat Market Oracle prices the token from on-chain scale factor + delinquency timer: grace → intermediary → final phase, token → ~0 by day 60.
- MLA (English law) gives lenders a legal claim; the oracle gives the vault a price feed. They run on separate tracks.
- The only thing stopping Wintermute defaulting is reputation — the mechanism itself offers zero protection. That is the single point of failure, and the moat, in one.

**Revenue streams for Zodia:**
1. **Funding spread** — SOFR+80 in, on-chain borrow rate out. Thin on vanilla supply (30–170 bps); the product only at self-referencing structures.
2. **Liquidation premium** — LIF ~5–6% bonus on seized collateral at 86% LLTV (capped 15%). Real money is what you do with the seized claim.
3. **Distressed-claims desk** — buy the claim at the oracle’s distressed price, hand to recovery specialists, keep the gap. A credit-recovery business wearing a DeFi costume.

The pitch line: *curation fees are a rounding error; a credit desk with its own engine earns the spread plus the liquidation premium — and the product only works if the collateral is self-referencing.*
