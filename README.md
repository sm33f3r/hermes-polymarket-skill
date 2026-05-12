# hermes-polymarket-skill

A Hermes Agent skill for trading on Polymarket.

This skill enables Hermes Agent to interact with Polymarket: browse markets, check wallet balances, and execute trades via the Polymarket CLOB v2 API. All trades are real-money transactions on Polygon mainnet. Hermes will always ask for explicit confirmation before executing any trade, ensuring you maintain full control over your trading activity.

## Prerequisites

- Hermes Agent installed and running
- A funded Polygon mainnet wallet (needs POL for gas, pUSD for trading)
- A Chainstack account with a Polygon mainnet node (free tier works)
- Python packages installed: `py_clob_client_v2`, `web3`, `requests`, `python-dotenv`

## Installation

```bash
hermes skills install https://github.com/sm33f3r/hermes-polymarket-skill
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `POLYMARKET_PRIVATE_KEY` | Required | EVM wallet private key for Polygon mainnet |
| `CHAINSTACK_NODE` | Required | Polygon mainnet RPC URL from Chainstack |
| `CLOB_API_KEY` | Auto-derived | Derived on first run — save to .env after first use |
| `CLOB_SECRET` | Auto-derived | Derived on first run — save to .env after first use |
| `CLOB_PASS_PHRASE` | Auto-derived | Derived on first run — save to .env after first use |

## First-Time Setup

1. Copy `.env.example` to `.env` and fill in `POLYMARKET_PRIVATE_KEY` and `CHAINSTACK_NODE`
2. Ask Hermes: `polymarket wallet status` — this derives and prints your CLOB API credentials on first run. Save them to `.env`
3. Ask Hermes: `polymarket wallet approve` — one-time CTF contract approval required before placing any buy orders
4. You are ready to trade

## Commands

| Command | Description |
|---------|-------------|
| `polymarket wallet status` | Show wallet address, POL balance, pUSD balance, CTF approval status |
| `polymarket wallet approve` | One-time CTF Exchange approval (required before first buy) |
| `polymarket markets trending` | Show top 10 markets by 24-hour volume |
| `polymarket markets search <query>` | Search active markets by keyword |
| `polymarket market <slug>` | Full market detail including token IDs for trading |
| `polymarket buy <token_id> <amount_usd>` | Place a market buy order (FOK) in pUSD |
| `polymarket sell <token_id> <amount>` | Place a market sell order (FAK) in shares |
| `polymarket positions` | Show open positions with current prices and unrealised P&L |

## Important Warnings

> This skill executes real trades with real money on Polygon mainnet.
> Always verify market name, direction, and amount before confirming a trade.
> Hermes will always ask for explicit confirmation before executing any buy or sell order.
> Never share your private key or commit your `.env` file to version control.

## License

MIT License. See [LICENSE](LICENSE) file for details.