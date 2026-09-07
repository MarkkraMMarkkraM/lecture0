# Onchain Credit Desk — slides v1 (source)

WORKING DRAFT · EXPLORATORY · NOT A DECISION

Binary deck: Drive — https://docs.google.com/presentation/d/1wzbEDmgsxFE33hCRkYN2KLvXz4yG3u0h/edit

---

## 01  ·  WHY A DESK NOW

**Connect the credit book to onchain credit portals**

Market has unbundled lending into isolated markets + curator vaults. Wintermute’s Armitage is the proof that a trading firm can sit on both sides of that stack.

**Morpho / vault layer**

Open credit network: isolated markets + third-party curators. ~$14bn deposits (Sep 2026). Vaults are the institutional / RWA rail.

**Aave still the pool**

Moat in blue-chip stablecoin and ETH liquidity. V4 hub-and-spoke is converging on isolated markets. Still the depth venue.

**Wintermute / Armitage**

May 2026: USDC Prime / Select on Morpho. Sep 2: USDT vaults, 0 fees. Uses own liquidation engine — collateral types others cannot take.

**What this means for a desk**

The product is not “list on Aave.” It is a permissioned front-end + credit process that allocates into curated vaults and isolated markets, with our own liquidation / risk overlay.

Peers already doing the mullet: Coinbase / Kraken / Fireblocks / Galaxy / Elwood route clients into Morpho vaults without the client touching DeFi UX.

Wintermute’s edge is liquidation + unsecured credit wrapping. Our edge, if any, is regulated credit process, banking/custody relationships, and existing OTC credit names.

01 / 03

---

## 02  ·  DESK DESIGN  ·  FROM OMI 2 SEP + 31 AUG

**A credit-portal desk, not another FX ramp**

Directors’ growth session (2 Sep): still exploratory. Scope named in the room — not approved.

**MANDATE**

Connect existing credit / liquidity book to Aave, Morpho (and peers) as portals — supply, borrow, vault deposit, curated strategies.

**RIGHT TO WIN**

Permissioned markets; banking and custody relationships already in place; ring-fenced non-regulated test entity if needed.

**PRODUCT STACK**

Collateralised lending · liquidity · DeFi / DEX lending · tokenised securities · funding-rate arb · liquidation services.

**ADJACENT LIVE COLOUR**

Treasury programme approved (3 Jul). BTC-backed lending path for named names (LTV / limit colour only). Cumberland credit authority is a live board path.

**DO NOT MIX**

Keep regulated credit process separate from any open DeFi execution. Independent Web3 / Aura stay on their own rails.

02 / 03

---

## 03  ·  STAND-UP PLAN  ·  GAPS FROM THE SAME NOTES

**What has to exist before the first vault ticket**

**Control stack**

- Named first-line owner — not second-line running the book
- Hard limits, throttles, overnight safeguards (RFS gap is the cautionary tale)
- LTV / liquidation playbook; Wintermute-style engine or explicit outsource
- Wallet lifecycle + inbound/outbound screening before protocol addresses go live
- Fireblocks / PMS path used as the settlement rail, not a side wallet

**Credit stack**

- Credit expertise flagged as thin (31 Aug) — hire or borrow it
- Vault / curator due diligence: Gauntlet, Steakhouse, Armitage, Galaxy…
- Protocol risk: oracle, isolation, curator mandate, fee, pause rights
- Counterparty map: Circle / Ripple / Cumberland style limits applied to vaults
- ERC-4626 vault + market allowlist; no permissionless browsing

**90-day test**

- Ring-fenced test entity, capped notional
- One stablecoin, two venues: Morpho blue-chip vault + Aave supply-only
- Paper the kill: depeg, curator drift, oracle failure, withdrawal queue
- No client money until ops/finance capacity and 10% risk-limit path exist
- Decision gate: keep / revise / kill after 90 days of observed liquidity

03 / 03
