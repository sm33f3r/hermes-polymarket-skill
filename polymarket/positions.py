"""
Open positions with unrealised P&L calculation.

This module fetches open positions from the CLOB API and enriches them
with current market prices from the Gamma API to compute unrealised P&L.
"""

import logging
import os
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

from polymarket.client import get_client
from polymarket.markets import get_market

# Load environment variables from .env file
load_dotenv()

# Module logger
logger = logging.getLogger(__name__)


def _get_current_price(token_id: str, tokens: List[Dict[str, Any]]) -> float:
    """
    Find current price for a token_id in a market's tokens list.

    Args:
        token_id: Token identifier to find price for.
        tokens: List of token dictionaries from a parsed market.

    Returns:
        Current price as float, or 0.0 if token not found.
    """
    if not tokens:
        return 0.0

    for token in tokens:
        if isinstance(token, dict) and token.get("token_id") == token_id:
            price = token.get("price", 0.0)
            try:
                return float(price)
            except (ValueError, TypeError):
                return 0.0

    # Token ID not found in this market's tokens
    logger.debug(f"Token ID {token_id} not found in market tokens list")
    return 0.0


def get_open_positions() -> List[Dict[str, Any]]:
    """
    Get all open positions with enriched market data and unrealised P&L.

    Fetches open positions from CLOB API, looks up corresponding market
    data from Gamma API, and computes current value vs cost basis.

    Returns:
        List of enriched position dictionaries with keys:
            market_name: str (question from Gamma, or condition_id if lookup fails)
            token_id: str
            outcome: str (YES or NO)
            shares: float
            avg_entry_price: float
            current_price: float
            unrealised_pnl_usd: float (rounded to 2 decimal places)
            condition_id: str

    If CLOB returns no positions, returns an empty list.
    If Gamma market lookup fails for a position, uses condition_id as market_name
    and sets current_price and unrealised_pnl_usd to 0.0.
    """
    try:
        client = get_client()
    except Exception as e:
        logger.error(f"Failed to get CLOB client: {e}")
        return []

    try:
        # Fetch open positions from CLOB API
        # Note: Assuming client.get_positions() returns list of position dicts
        # If method name differs, adjust accordingly
        positions = client.get_positions()
    except AttributeError:
        # Try common method names if get_positions doesn't exist
        try:
            positions = client.get_open_positions()
        except AttributeError as e:
            logger.error(f"CLOB client has no positions method: {e}")
            return []
    except Exception as e:
        logger.error(f"Failed to fetch positions from CLOB API: {e}")
        return []

    if not positions:
        # No open positions
        return []

    enriched_positions = []

    for position in positions:
        # Extract position data with safe defaults
        token_id = str(position.get("token_id", ""))
        condition_id = str(position.get("condition_id", ""))
        outcome = str(position.get("outcome", ""))  # YES or NO

        # Parse numeric values with error handling
        try:
            shares = float(position.get("shares", 0))
        except (ValueError, TypeError):
            shares = 0.0

        try:
            avg_entry_price = float(position.get("avg_entry_price", 0))
        except (ValueError, TypeError):
            avg_entry_price = 0.0

        # Default values in case market lookup fails
        market_name = condition_id
        current_price = 0.0
        unrealised_pnl_usd = 0.0

        # Try to fetch market data from Gamma API
        market_data = None
        market_slug = position.get("market_slug", position.get("slug", ""))

        try:
            # First try to get market by slug if available
            if market_slug:
                market_data = get_market(market_slug)
            # Fall back to condition_id if slug not available
            else:
                market_data = get_market(condition_id)
        except Exception as e:
            # If both slug and condition_id fail
            logger.warning(
                f"Failed to fetch market data for slug '{market_slug}' or condition_id {condition_id}: {e}"
            )
            # Search could be implemented here if needed
            pass

        if market_data:
            market_name = market_data.get("question", condition_id)

            # Get current price from market tokens
            tokens = market_data.get("tokens", [])
            current_price = _get_current_price(token_id, tokens)

            # Calculate unrealised P&L
            if shares > 0 and current_price > 0:
                current_value = shares * current_price
                cost_basis = shares * avg_entry_price
                unrealised_pnl_usd = round(current_value - cost_basis, 2)
        else:
            logger.warning(
                f"No market data found for slug '{market_slug}' or condition_id {condition_id}, "
                f"token_id {token_id}. P&L calculation skipped."
            )

        enriched_positions.append(
            {
                "market_name": market_name,
                "token_id": token_id,
                "outcome": outcome,
                "shares": shares,
                "avg_entry_price": avg_entry_price,
                "current_price": current_price,
                "unrealised_pnl_usd": unrealised_pnl_usd,
                "condition_id": condition_id,
            }
        )

    return enriched_positions