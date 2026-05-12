"""
On-chain wallet data for Polymarket.

This module handles native POL and pUSD ERC-20 balances, and CTF approval status.
Uses web3.py with Chainstack RPC node — independent of CLOB client.
"""

import os
from typing import Dict, Any

from dotenv import load_dotenv
from web3 import Web3
from web3.contract import Contract

from polymarket.client import get_wallet_address

# Load environment variables from .env file
load_dotenv()

# Constants
PUSD_CONTRACT_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
PUSD_DECIMALS = 6
CTF_EXCHANGE_ADDRESS = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

# Minimal ERC-20 ABI for balanceOf and allowance functions
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function",
    },
]

# Initialize Web3 connection to Polygon mainnet
CHAINSTACK_NODE = os.getenv("CHAINSTACK_NODE")
if not CHAINSTACK_NODE:
    raise RuntimeError(
        "CHAINSTACK_NODE environment variable is required for on-chain data. "
        "Set it to your Chainstack RPC endpoint URL."
    )

w3 = Web3(Web3.HTTPProvider(CHAINSTACK_NODE))
if not w3.is_connected():
    raise RuntimeError(f"Failed to connect to Chainstack node: {CHAINSTACK_NODE}")

# Initialize pUSD ERC-20 contract with checksummed address
pusd_contract_address = w3.to_checksum_address(PUSD_CONTRACT_ADDRESS)
ctf_exchange_address = w3.to_checksum_address(CTF_EXCHANGE_ADDRESS)
pusd_contract: Contract = w3.eth.contract(
    address=pusd_contract_address,
    abi=ERC20_ABI,
)


def get_pol_balance(address: str) -> float:
    """
    Fetch native POL balance for a given address.

    Args:
        address: Ethereum address (any format) to check balance for.

    Returns:
        POL balance as float, rounded to 6 decimal places.

    Raises:
        ValueError: If address format is invalid.
    """
    try:
        checksum_address = w3.to_checksum_address(address)
    except ValueError as e:
        raise ValueError(f"Invalid Ethereum address '{address}': {e}")

    # Get balance in wei
    balance_wei = w3.eth.get_balance(checksum_address)

    # Convert to POL (MATIC) - 1 POL = 10^18 wei
    balance_pol = w3.from_wei(balance_wei, "ether")

    # Round to 6 decimal places for readability
    return round(float(balance_pol), 6)


def get_pusd_balance(address: str) -> float:
    """
    Fetch pUSD ERC-20 balance for a given address.

    Args:
        address: Ethereum address (any format) to check pUSD balance for.

    Returns:
        pUSD balance as float, rounded to 2 decimal places.

    Raises:
        ValueError: If address format is invalid.
    """
    try:
        checksum_address = w3.to_checksum_address(address)
    except ValueError as e:
        raise ValueError(f"Invalid Ethereum address '{address}': {e}")

    # Call balanceOf on pUSD contract
    raw_balance = pusd_contract.functions.balanceOf(checksum_address).call()

    # Convert from raw units to pUSD (6 decimals)
    balance_pusd = raw_balance / (10**PUSD_DECIMALS)

    # Round to 2 decimal places for currency display
    return round(float(balance_pusd), 2)


def get_ctf_approval_status(address: str) -> bool:
    """
    Check if pUSD contract is approved for spending by CTF Exchange.

    Args:
        address: Ethereum address (any format) to check approval for.

    Returns:
        True if allowance > 0, False otherwise.

    Raises:
        ValueError: If address format is invalid.
    """
    try:
        checksum_address = w3.to_checksum_address(address)
    except ValueError as e:
        raise ValueError(f"Invalid Ethereum address '{address}': {e}")

    # Note: checks pUSD allowance as a proxy for CTF approval.
    # Full CTF (ERC-1155) approval is handled by trading.py via the CLOB client.
    allowance_raw = pusd_contract.functions.allowance(
        checksum_address, ctf_exchange_address
    ).call()

    # Approval exists if allowance > 0
    return allowance_raw > 0


def get_wallet_status() -> Dict[str, Any]:
    """
    Convenience function to get comprehensive wallet status.

    Retrieves wallet address from client.py, then fetches:
    - POL balance (native MATIC)
    - pUSD balance (ERC-20)
    - CTF Exchange approval status

    Returns:
        Dictionary with keys:
            address: str (checksummed wallet address)
            pol_balance: float
            pusd_balance: float
            ctf_approved: bool
    """
    # Get wallet address from client.py
    address = get_wallet_address()

    # Fetch all wallet data
    pol_balance = get_pol_balance(address)
    pusd_balance = get_pusd_balance(address)
    ctf_approved = get_ctf_approval_status(address)

    return {
        "address": w3.to_checksum_address(address),
        "pol_balance": pol_balance,
        "pusd_balance": pusd_balance,
        "ctf_approved": ctf_approved,
    }