"""
Polymarket CLOB API client wrapper.

This module provides a singleton authenticated ClobClient instance for all
Polymarket trading operations. Handles L1+L2 authentication bootstrapping.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from py_clob_client_v2 import ClobClient
from py_clob_client_v2 import ApiCreds
from web3 import Web3

# Load environment variables from .env file
load_dotenv()

# Constants
CLOB_HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon mainnet

# Module-level client cache
_client: Optional[ClobClient] = None


def get_client() -> ClobClient:
    """
    Return a singleton authenticated ClobClient instance.

    Authentication flow:
    1. If CLOB_API_KEY, CLOB_SECRET, and CLOB_PASS_PHRASE are present in environment,
       build a fully-authenticated L1+L2 client immediately.
    2. If credentials are missing, build an L1-only client using POLYMARKET_PRIVATE_KEY,
       derive API credentials via create_or_derive_api_key(), print them for the user
       to save to .env, then rebuild as fully-authenticated client.
    3. Cache and return the authenticated client.

    Returns:
        Authenticated ClobClient instance ready for trading.

    Raises:
        RuntimeError: If POLYMARKET_PRIVATE_KEY is missing from environment.
    """
    global _client

    if _client is not None:
        return _client

    # Check for existing API credentials
    api_key = os.getenv("CLOB_API_KEY")
    api_secret = os.getenv("CLOB_SECRET")
    api_passphrase = os.getenv("CLOB_PASS_PHRASE")

    # Get private key - required for all authentication paths
    private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
    if not private_key:
        raise RuntimeError(
            "POLYMARKET_PRIVATE_KEY environment variable is required. "
            "Set it to your wallet's private key (without 0x prefix)."
        )

    if api_key and api_secret and api_passphrase:
        # Build fully-authenticated client with existing credentials
        creds = Creds(
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
            private_key=private_key,
        )
        _client = ClobClient(
            host=CLOB_HOST,
            chain_id=CHAIN_ID,
            key=private_key,
            creds=creds,
        )
    else:
        # Build L1-only client and derive credentials
        print("CLOB API credentials not found. Deriving new credentials...")
        l1_client = ClobClient(
            host=CLOB_HOST,
            chain_id=CHAIN_ID,
            private_key=private_key,
        )

        # Derive API credentials
        derived_creds = l1_client.create_or_derive_api_key()
        print("\n" + "=" * 60)
        print("SAVE THESE CREDENTIALS TO YOUR .env FILE:")
        print("=" * 60)
        print(f"CLOB_API_KEY={derived_creds.api_key}")
        print(f"CLOB_SECRET={derived_creds.api_secret}")
        print(f"CLOB_PASS_PHRASE={derived_creds.api_passphrase}")
        print("=" * 60)
        print("Add these lines to your .env file to avoid re-deriving.")
        print("=" * 60 + "\n")

        # Build fully-authenticated client with derived credentials
        creds = Creds(
            api_key=derived_creds.api_key,
            api_secret=derived_creds.api_secret,
            api_passphrase=derived_creds.api_passphrase,
            private_key=private_key,
        )
        _client = ClobClient(
            host=CLOB_HOST,
            chain_id=CHAIN_ID,
            key=private_key,
            creds=creds,
        )

    return _client


def get_wallet_address() -> str:
    """
    Derive and return the checksum wallet address from POLYMARKET_PRIVATE_KEY.

    Uses web3.py to derive the public address from the private key.
    No RPC call is needed — purely local computation.

    Returns:
        Checksum-formatted Ethereum address (0x-prefixed).

    Raises:
        RuntimeError: If POLYMARKET_PRIVATE_KEY is missing or invalid.
    """
    private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
    if not private_key:
        raise RuntimeError(
            "POLYMARKET_PRIVATE_KEY environment variable is required. "
            "Set it to your wallet's private key (without 0x prefix)."
        )

    # Ensure private key doesn't have 0x prefix
    if private_key.startswith("0x"):
        private_key = private_key[2:]

    # Derive address from private key
    w3 = Web3()
    try:
        account = w3.eth.account.from_key(private_key)
        return w3.to_checksum_address(account.address)
    except Exception as e:
        raise RuntimeError(f"Failed to derive wallet address: {e}")


# For backwards compatibility and clarity
get_wallet = get_wallet_address