# hermes-polymarket-skill

A Hermes Agent skill for trading on Polymarket via the CLOB v2 API.

This skill enables Hermes to browse markets, check wallet balances, and
execute real-money trades on Polymarket (Polygon mainnet). Hermes will
always ask for explicit confirmation before executing any trade.

## Prerequisites

- Hermes Agent installed and running
- A Polymarket account with:
  - An EOA wallet (private key)
  - A Polymarket deposit wallet address
  - CLOB builder API credentials (key, secret, passphrase)
- A Polygon mainnet RPC URL (Chainstack free tier works)
- Node.js v18 or higher on the host machine
- Python 3.9 or higher

## Installation

```bash
hermes skills install https://github.com/sm33f3r/hermes-polymarket-skill
cd /path/to/skill
npm install
```

## Environment Variables

Set all of the following before using the skill:

| Variable | Description |
|----------|-------------|
| `POLYMARKET_PRIVATE_KEY` | EOA wallet private key (Polygon mainnet) |
| `POLYMARKET_PROXY_ADDRESS` | Your Polymarket deposit wallet address |
| `CLOB_API_KEY` | CLOB builder API key |
| `CLOB_SECRET` | CLOB builder secret |
| `CLOB_PASS_PHRASE` | CLOB builder passphrase |
| `CHAINSTACK_NODE` | Polygon mainnet RPC URL |

## Setup

1. Clone the repo and run `npm install`
2. Set all six environment variables above
3. Fund your deposit wallet with pUSD via the Polymarket UI
4. You are ready to trade

## Commands

| Command | Description |
|---------|-------------|
| `polymarket wallet status` | Wallet address, POL balance, pUSD balance |
| `polymarket markets trending` | Top 10 markets by 24-hour volume |
| `polymarket markets search <query>` | Search active markets by keyword |
| `polymarket market <slug>` | Full market detail including token IDs |
| `polymarket buy <token_id> <amount_usd>` | Market buy order (FOK) in pUSD |
| `polymarket sell <token_id> <amount_shares>` | Market sell order (FOK) in shares |
| `polymarket positions` | Open positions for the deposit wallet |

## Architecture
Hermes Agent (Python)
└── trading.py          # Thin subprocess wrapper
└── polymarket_exec.js   # Node.js CLOB v2 execution layer
└── @polymarket/clob-client-v2

Public market data (wallet status, market search, positions) is fetched
directly from the Polymarket Gamma API with no authentication required.
Order execution routes through `polymarket_exec.js` via subprocess.

## Important Warnings

> This skill executes real trades with real money on Polygon mainnet.
> Always verify market name, direction, and amount before confirming a trade.
> Hermes will always ask for explicit confirmation before executing any order.
> Never share your private key or commit it to version control.

## License

MIT