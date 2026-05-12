"""
Polymarket Gamma API client for market data.

This module fetches market data from the public Polymarket Gamma REST API.
No authentication required.
"""

import json
import os
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Constants
GAMMA_API_BASE = "https://gamma-api.polymarket.com"
DEFAULT_LIMIT = 10
REQUEST_TIMEOUT = 10  # seconds


def _get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Internal helper to make GET requests to Gamma API.

    Args:
        endpoint: API endpoint path (e.g., "/markets")
        params: Query parameters for the request

    Returns:
        Parsed JSON response as dictionary.

    Raises:
        RuntimeError: If the response status is not 200.
    """
    url = f"{GAMMA_API_BASE}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            raise RuntimeError(
                f"Gamma API request failed: {response.status_code} - {response.text}"
            )
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request to Gamma API failed: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Gamma API response as JSON: {e}") from e


def _parse_market(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse raw market data from Gamma API into a clean, consistent format.

    Args:
        raw: Raw market dictionary from Gamma API.

    Returns:
        Clean market dictionary with standardized keys and types.
    """
    # Helper to parse JSON strings if needed
    def _maybe_parse_json(value: Any, default: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        elif value is None:
            return default
        return value

    # Parse outcomes (may be JSON string or list)
    raw_outcomes = raw.get("outcomes", [])
    outcomes = _maybe_parse_json(raw_outcomes, [])

    # Parse outcome prices (may be JSON string or list)
    raw_outcome_prices = raw.get("outcomePrices", [])
    outcome_prices_raw = _maybe_parse_json(raw_outcome_prices, [])

    # Convert prices to floats and round to 4 decimal places
    outcome_prices = []
    for price in outcome_prices_raw:
        try:
            parsed_price = float(price)
            outcome_prices.append(round(parsed_price, 4))
        except (ValueError, TypeError):
            outcome_prices.append(0.0)

    # Parse tokens array
    tokens = raw.get("tokens", [])
    if isinstance(tokens, str):
        try:
            tokens = json.loads(tokens)
        except json.JSONDecodeError:
            tokens = []

    # Clean token objects
    clean_tokens = []
    for token in tokens:
        if isinstance(token, dict):
            clean_tokens.append(
                {
                    "token_id": token.get("token_id", ""),
                    "outcome": token.get("outcome", ""),
                    "price": float(token.get("price", 0.0)),
                }
            )

    # Extract volume with default
    volume_raw = raw.get("volume", 0)
    try:
        volume = float(volume_raw)
    except (ValueError, TypeError):
        volume = 0.0

    return {
        "slug": raw.get("slug", ""),
        "question": raw.get("question", ""),
        "outcomes": outcomes,
        "outcome_prices": outcome_prices,
        "volume": volume,
        "end_date": raw.get("endDate"),  # Keep as None if missing
        "condition_id": raw.get("conditionId", ""),
        "tokens": clean_tokens,
    }


def get_trending_markets(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """
    Get trending markets sorted by 24-hour volume.

    Args:
        limit: Maximum number of markets to return.

    Returns:
        List of parsed market dictionaries.
    """
    params = {
        "order": "volume24hr",
        "ascending": "false",
        "limit": limit,
        "active": "true",
    }
    response = _get("/markets", params=params)

    markets = response.get("data", [])
    parsed_markets = [_parse_market(market) for market in markets]

    return parsed_markets


def search_markets(query: str, limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """
    Search markets by question text.

    Args:
        query: Search query string.
        limit: Maximum number of markets to return.

    Returns:
        List of parsed market dictionaries matching the query.
    """
    params = {
        "q": query,
        "active": "true",
        "limit": limit,
    }
    response = _get("/markets", params=params)

    markets = response.get("data", [])
    parsed_markets = [_parse_market(market) for market in markets]

    return parsed_markets


def get_market(slug: str) -> Dict[str, Any]:
    """
    Get a single market by its slug.

    Args:
        slug: Market slug identifier (e.g., "will-trump-win-2024").

    Returns:
        Parsed market dictionary.

    Raises:
        RuntimeError: If no market found for the given slug.
    """
    params = {"slug": slug}
    response = _get("/markets", params=params)

    markets = response.get("data", [])
    if not markets:
        raise RuntimeError(f"No market found with slug: {slug}")

    # Return first (and should be only) market
    return _parse_market(markets[0])