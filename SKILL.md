---
name: polymarket
version: 2.0.0
description: Trade on Polymarket — browse markets, check wallet balances, and execute orders via the CLOB v2 API
author: sm33f3r
tags: [trading, polymarket, defi, prediction-markets]
required_env:
  - POLYMARKET_PRIVATE_KEY
  - POLYMARKET_PROXY_ADDRESS
  - CLOB_API_KEY
  - CLOB_SECRET
  - CLOB_PASS_PHRASE
  - CHAINSTACK_NODE
---

# Polymarket Skill

You have access to Polymarket — a real-money prediction market platform on
Polygon mainnet. This skill gives you the ability to browse markets, check
wallet balances, and execute trades. All trades involve real funds. Act with
discipline and always confirm trade details with the user before executing.

## Environment setup

The following environment variables must be set before any command will work:

- `POLYMARKET_PRIVATE_KEY` — EOA wallet private key (Polygon mainnet)
- `POLYMARKET_PROXY_ADDRESS` — Deposit wallet address (the address Polymarket debits for trades)
- `CLOB_API_KEY` — CLOB builder API key
- `CLOB_SECRET` — CLOB builder secret
- `CLOB_PASS_PHRASE` — CLOB builder passphrase
- `CHAINSTACK_NODE` — Polygon mainnet RPC URL


## How to run commands

All commands are executed via the terminal tool using Python. Import and call
the relevant module function directly. Example:

```python
import sys
sys.path.insert(0, '/path/to/hermes-polymarket-skill')
from polymarket.wallet import get_wallet_status
result = get_wallet_status()
print(result)
```

Always print results so they appear in the terminal output.

---

## Commands

### polymarket wallet status

Returns the wallet address, POL balance, and pUSD balance.

```python
from polymarket.wallet import get_wallet_status
result = get_wallet_status()
print(result)
```

Returns dict with keys: `address`, `pol_balance`, `pusd_balance`, `ctf_approved`

Present to the user as:
```
Wallet: 0x...
POL balance: X.XXXXXX
pUSD balance: X.XX
CTF approved: Yes / No
```


---

### polymarket markets trending [--limit N]

Returns top markets by 24-hour volume. Default limit is 10.

```python
from polymarket.markets import get_trending_markets
markets = get_trending_markets(limit=10)
for m in markets:
    print(m)
```

Present each market as:
```
Market: [question]
Slug: [slug]
YES: [outcome_prices[0]] | NO: [outcome_prices[1]]
Volume: $[volume]
Ends: [end_date]
```

---

### polymarket markets search <query>

Search active markets by keyword.

```python
from polymarket.markets import search_markets
markets = search_markets(query="your search term", limit=10)
for m in markets:
    print(m)
```

Present results in the same format as trending markets.

---

### polymarket market <slug>

Full market detail for a single market. Always run this before placing a buy
or sell order — the token IDs returned here are required for trading commands.

```python
from polymarket.markets import get_market
market = get_market(slug="market-slug-here")
print(market)
```

Present as:
```
Market: [question]
Ends: [end_date]
Volume: $[volume]

Outcomes:
  YES — Price: [tokens[0].price] | Token ID: [tokens[0].token_id]
  NO  — Price: [tokens[1].price] | Token ID: [tokens[1].token_id]
```

Always show the token IDs — the user will need them for buy/sell commands.

---

### polymarket buy <token_id> <amount_usd>

Places a FOK (Fill or Kill) market buy order. amount_usd is in pUSD.

IMPORTANT: Always confirm the following with the user before executing:
- Market name and direction (YES or NO)
- Amount in pUSD
- Current price / implied probability
- That sufficient pUSD balance is available

Only execute after explicit user confirmation.

```python
from polymarket.trading import market_buy
result = market_buy(token_id="token-id-here", amount_usd=50.0)
print(result)
```

Present the result as:
```
Order submitted.
Status: [result.status]
Filled: [result.filled_amount] shares at [result.price]
Order ID: [result.order_id]
```

If the order is not filled (FOK cancelled), inform the user clearly and suggest
they check current liquidity or try a smaller amount.

---

### polymarket sell <token_id> <amount>

Places a FAK (Fill and Kill) market sell order. amount is in shares.

IMPORTANT: Always confirm the following with the user before executing:
- Market name and direction being sold
- Number of shares
- Current price
- Expected proceeds in pUSD

Only execute after explicit user confirmation.

```python
from polymarket.trading import market_sell
result = market_sell(token_id="token-id-here", amount_shares=100.0)
print(result)
```

Present the result in the same format as a buy order result. If only partially
filled (FAK), report how many shares were sold and how many remain.

---

### polymarket positions

Returns all open positions with current prices and unrealised P&L.

```python
from polymarket.positions import get_open_positions
positions = get_open_positions()
for p in positions:
    print(p)
```

Present each position as:
```
Market: [market_name]
Direction: [outcome]
Shares: [shares] @ avg entry [avg_entry_price]
Current price: [current_price]
Unrealised P&L: [unrealised_pnl_usd] pUSD
```

If no open positions, say so clearly.

---

## Error handling guidance

- If a buy or sell command returns `{"ok": false, "error": "..."}`: surface
  the error message to the user and wait for instruction.
- If the error contains "Node exited": the Node.js script failed to start.
  Check that POLYMARKET_PRIVATE_KEY and all CLOB credentials are set correctly.
- If a FOK order is not filled: liquidity is insufficient at the current price.
  Inform the user and do not retry automatically.
- If Gamma API calls fail: check internet connectivity. The Gamma API is public
  and requires no authentication.
- Never retry a failed order automatically. Always surface the error to the
  user and wait for instruction.

## Important warnings

- This skill executes real trades with real money on Polygon mainnet.
- Always confirm position sizing and direction with the user before executing
  any buy or sell command.
- Never execute a trade without explicit user confirmation in the current
  session.
- Never store or log the user's private key.
