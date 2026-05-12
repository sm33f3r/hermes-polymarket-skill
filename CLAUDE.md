# CLAUDE.md

This file provides guidance to AI coding agents working in this repository.

## What this repo is

A Hermes Agent skill that gives Hermes the ability to interact with Polymarket:
browse markets, check wallet balances, and execute trades via the Polymarket
CLOB v2 API.

This is a public, open-source repository intended for use by any Hermes Agent
user. Code and documentation must be written to that standard — clean,
well-commented, no hardcoded values, no project-specific references.

## Repo structure

```
hermes-polymarket-skill/
├── CLAUDE.md               ← This file
├── SKILL.md                ← Hermes skill definition (frontmatter + instructions)
├── README.md               ← Public documentation
├── requirements.txt        ← Python dependencies
├── .gitignore              ← Standard Python gitignore
├── .env.example            ← Environment variable template
└── polymarket/
    ├── __init__.py         ← Package init (empty)
    ├── client.py           ← ClobClient wrapper + credential bootstrap
    ├── markets.py          ← Gamma API (market search, trending, detail)
    ├── trading.py          ← buy, sell, approve
    ├── positions.py        ← open positions with live P&L
    └── wallet.py           ← balances (POL + pUSD), wallet address
```

## Key dependencies

- `py_clob_client_v2` — official Polymarket CLOB v2 Python client
- `web3>=6.0.0` — on-chain balance checks via Chainstack RPC
- `requests` — Gamma API calls (no auth required)
- `python-dotenv` — environment variable loading

## APIs used

### Polymarket Gamma API (market data — no auth)
Base URL: `https://gamma-api.polymarket.com`
- `GET /markets` — list, search, filter markets
- Fields of interest: slug, question, outcomes, outcomePrices, volume,
  endDate, conditionId, tokens (array of {token_id, outcome, price})

### Polymarket CLOB API (order execution — L1 + L2 auth)
Base URL: `https://clob.polymarket.com`
- Wrapped by `py_clob_client_v2.ClobClient`
- L1 auth: wallet private key (EIP-712)
- L2 auth: derived API key/secret/passphrase (HMAC)

### Polygon mainnet RPC (on-chain reads)
- Provided via `CHAINSTACK_NODE` environment variable
- Used for: POL balance, pUSD ERC-20 balance, CTF approval status

## Important contract addresses (Polygon mainnet)

- pUSD token: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` (6 decimals)
- CTF Exchange: `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E`

## Authentication flow

On first run (no CLOB_API_KEY in environment):
1. Build L1-only client using POLYMARKET_PRIVATE_KEY
2. Call `client.create_or_derive_api_key()`
3. Print derived credentials clearly so user can save them to .env
4. Cache credentials for the current session

On subsequent runs (CLOB_API_KEY present in environment):
1. Load credentials from environment
2. Build fully-authenticated L1+L2 client immediately

All modules that need an authenticated client import `get_client()` from
`polymarket/client.py`.

## Order types

- `FOK` (Fill or Kill) — used for buy orders. Must fill completely or cancel.
- `FAK` (Fill and Kill) — used for sell orders. Fills what it can, cancels rest.
- Never use `GTC` (resting limit orders) — we want immediate execution only.

## Code standards

- Type hints on all function signatures
- Docstrings on all public functions
- No hardcoded values — everything via environment variables or constants
  defined at the top of each module
- Errors should raise with descriptive messages, not fail silently
- All amounts: input in human-readable form (pUSD), convert to raw units
  internally before API calls
- Never log or print private keys or API secrets

## Build order

Files are built one at a time in this sequence:
1. `.gitignore`
2. `requirements.txt`
3. `.env.example`
4. `polymarket/__init__.py`
5. `polymarket/client.py`
6. `polymarket/wallet.py`
7. `polymarket/markets.py`
8. `polymarket/positions.py`
9. `polymarket/trading.py`
10. `SKILL.md`
11. `README.md`

Do not skip ahead. Do not modify files that have already been reviewed and
approved unless specifically instructed.

## Git

- Work on main branch only
- Commit after each file is approved, not in bulk at the end
- Commit message format: `add <filename>: <one line description>`