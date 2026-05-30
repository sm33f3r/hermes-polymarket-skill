"""
Polymarket order execution via Node.js subprocess wrapper.

This module provides a thin Python interface to the polymarket_exec.js
Node.js script, which handles all CLOB API interactions.
"""

import subprocess
import json
import logging

# Constants
EXEC_SCRIPT = "/opt/data/skills/polymarket/polymarket_exec.js"
NODE_BIN = "/usr/bin/node"

# Module logger
logger = logging.getLogger(__name__)


def _call_node(cmd_dict: dict) -> dict:
    """
    Internal helper to call the Node.js script with a command dict.

    Args:
        cmd_dict: Command dictionary to send to polymarket_exec.js

    Returns:
        Parsed JSON response from the script, or error dict on failure.
    """
    try:
        # Build the subprocess command
        cmd_json = json.dumps(cmd_dict)
        result = subprocess.run(
            [NODE_BIN, EXEC_SCRIPT, cmd_json],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Handle non-zero exit code when stdout is empty
        if result.returncode != 0 and not result.stdout.strip():
            return {
                "ok": False,
                "error": f"Node exited {result.returncode}: {result.stderr}"
            }

        # Parse and return the JSON response
        return json.loads(result.stdout)

    except Exception as e:
        return {"ok": False, "error": str(e)}


def market_buy(token_id: str, amount_usd: float) -> dict:
    """
    Buy amount_usd pUSD worth of token_id.

    Args:
        token_id: Token identifier to buy
        amount_usd: Amount to spend in pUSD

    Returns:
        Order result dictionary from CLOB API
    """
    logger.info(f"Market buy: token_id={token_id}, amount_usd={amount_usd}")

    cmd = {
        "command": "buy",
        "token_id": token_id,
        "amount_usd": amount_usd
    }

    return _call_node(cmd)


def market_sell(token_id: str, amount_shares: float) -> dict:
    """
    Sell amount_shares of token_id.

    Args:
        token_id: Token identifier to sell
        amount_shares: Amount to sell in shares

    Returns:
        Order result dictionary from CLOB API
    """
    logger.info(f"Market sell: token_id={token_id}, amount_shares={amount_shares}")

    cmd = {
        "command": "sell",
        "token_id": token_id,
        "amount_shares": amount_shares
    }

    return _call_node(cmd)


def get_balance() -> dict:
    """
    Get current pUSD balance of deposit wallet.

    Returns:
        Balance dictionary with 'balance_usd' field
    """
    logger.info("Getting balance")

    cmd = {"command": "balance"}
    return _call_node(cmd)


def get_positions() -> dict:
    """
    Get open positions for deposit wallet.

    Returns:
        Positions dictionary with 'positions' field
    """
    logger.info("Getting positions")

    cmd = {"command": "positions"}
    return _call_node(cmd)


if __name__ == "__main__":
    import json
    print(json.dumps(get_balance(), indent=2))