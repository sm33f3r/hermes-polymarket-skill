"""
Polymarket order execution via CLOB API.

This module handles CTF approval, market buy orders, and market sell orders
using the authenticated CLOB client.
"""

import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
from py_clob_client_v2 import (
    MarketOrderArgs,
    Side,
    OrderType,
    PartialCreateOrderOptions,
)

from polymarket.client import get_client

# Load environment variables from .env file
load_dotenv()

# Module logger
logger = logging.getLogger(__name__)


def approve_ctf() -> Dict[str, Any]:
    """
    Approve the CTF Exchange contract to spend conditional tokens.

    This is a one-time operation required before any buy order will succeed.
    Uses client.set_allowances() if available, otherwise tries
    client.approve_ctf_exchange().

    Returns:
        Raw response dictionary from the client.

    Raises:
        RuntimeError: If the approval operation fails.
    """
    logger.info("Approving CTF Exchange contract for conditional token spending...")

    try:
        client = get_client()
    except Exception as e:
        raise RuntimeError(f"Failed to get authenticated CLOB client: {e}") from e

    try:
        # Try set_allowances() first
        if hasattr(client, "set_allowances"):
            result = client.set_allowances()
            logger.info("set_allowances() completed successfully.")
        elif hasattr(client, "approve_ctf_exchange"):
            result = client.approve_ctf_exchange()
            logger.info("approve_ctf_exchange() completed successfully.")
        else:
            raise RuntimeError(
                "CLOB client has no CTF approval methods (set_allowances or approve_ctf_exchange)."
            )

        logger.info("CTF Exchange contract approved for conditional token spending.")
        return result

    except Exception as e:
        error_msg = f"Failed to approve CTF Exchange contract: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def market_buy(token_id: str, amount_usd: float, tick_size: str = "0.01") -> Dict[str, Any]:
    """
    Place a FOK (Fill or Kill) market buy order.

    Args:
        token_id: Token identifier to buy.
        amount_usd: Amount to spend in pUSD (not converted).
        tick_size: Minimum price increment (default "0.01").

    Returns:
        Raw response dictionary from the client.

    Raises:
        RuntimeError: If the buy order fails.
    """
    logger.info(f"Placing market buy order: token_id={token_id}, amount_usd={amount_usd}, tick_size={tick_size}")

    try:
        client = get_client()
    except Exception as e:
        raise RuntimeError(f"Failed to get authenticated CLOB client: {e}") from e

    try:
        # Construct market order arguments
        order_args = MarketOrderArgs(
            token_id=token_id,
            amount=amount_usd,
            side=Side.BUY,
        )

        # Construct order options
        options = PartialCreateOrderOptions(tick_size=tick_size)

        # Execute market buy order (FOK)
        result = client.create_and_post_market_order(
            order_type=OrderType.FOK,
            market_order=order_args,
            options=options,
        )

        logger.info(f"Market buy order submitted successfully for token_id={token_id}")
        return result

    except Exception as e:
        error_msg = f"Market buy order failed for token_id={token_id}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def market_sell(token_id: str, amount: float, tick_size: str = "0.01") -> Dict[str, Any]:
    """
    Place a FAK (Fill and Kill) market sell order.

    Args:
        token_id: Token identifier to sell.
        amount: Amount to sell in shares (not converted).
        tick_size: Minimum price increment (default "0.01").

    Returns:
        Raw response dictionary from the client.

    Raises:
        RuntimeError: If the sell order fails.
    """
    logger.info(f"Placing market sell order: token_id={token_id}, amount={amount}, tick_size={tick_size}")

    try:
        client = get_client()
    except Exception as e:
        raise RuntimeError(f"Failed to get authenticated CLOB client: {e}") from e

    try:
        # Construct market order arguments
        order_args = MarketOrderArgs(
            token_id=token_id,
            amount=amount,
            side=Side.SELL,
        )

        # Construct order options
        options = PartialCreateOrderOptions(tick_size=tick_size)

        # Execute market sell order (FAK)
        result = client.create_and_post_market_order(
            order_type=OrderType.FAK,
            market_order=order_args,
            options=options,
        )

        logger.info(f"Market sell order submitted successfully for token_id={token_id}")
        return result

    except Exception as e:
        error_msg = f"Market sell order failed for token_id={token_id}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e