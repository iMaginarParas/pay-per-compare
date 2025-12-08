import os
from dotenv import load_dotenv
from web3 import Web3
from eth_utils import to_checksum_address
from fastapi import Header, HTTPException

# Ensure env vars are loaded when this module is imported
load_dotenv()

# --- CONFIGURATION ---
AVAX_RPC_URL = "https://api.avax-test.network/ext/bc/C/rpc"
w3 = Web3(Web3.HTTPProvider(AVAX_RPC_URL))

# Accessing env vars safely with fallbacks or direct access
RECEIVING_WALLET_ADDRESS = to_checksum_address(os.getenv("RECEIVING_WALLET_ADDRESS"))
USDC_CONTRACT_ADDRESS = to_checksum_address(os.getenv("USDC_CONTRACT_ADDRESS"))

# Store used hashes to prevent replay attacks
USED_TRANSACTION_HASHES = set()

# Minimal ABI to decode the "Transfer" event
ERC20_TRANSFER_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "from", "type": "address"},
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": False, "name": "value", "type": "uint256"},
    ],
    "name": "Transfer",
    "type": "event",
}

async def verify_usdc_payment(
    required_amount_usd: float,
    x_payment_tx: str = Header(..., alias="X-Payment-Tx")
):
    """
    Dependency function to verify USDC payment on Avalanche Fuji.
    Now accepts dynamic amount based on model cost.
    
    Args:
        required_amount_usd: Required payment in USD (e.g., 0.03 for SDXL)
        x_payment_tx: Transaction hash from header
    """
    # Convert USD to USDC units (6 decimals)
    required_usdc_units = int(required_amount_usd * 10**6)
    
    if x_payment_tx in USED_TRANSACTION_HASHES:
        raise HTTPException(status_code=402, detail="Payment hash already used.")

    try:
        tx_receipt = w3.eth.get_transaction_receipt(x_payment_tx)
    except Exception:
        raise HTTPException(status_code=402, detail="Transaction not found.")

    if tx_receipt['status'] != 1:
        raise HTTPException(status_code=402, detail="Transaction failed on-chain.")

    # Parse logs to find the Transfer event
    contract = w3.eth.contract(address=USDC_CONTRACT_ADDRESS, abi=[ERC20_TRANSFER_EVENT_ABI])
    transfers = contract.events.Transfer().process_receipt(tx_receipt)

    payment_found = False
    
    for transfer in transfers:
        # Check if money was sent TO us
        if transfer['args']['to'] == RECEIVING_WALLET_ADDRESS:
            # Check amount
            if transfer['args']['value'] >= required_usdc_units:
                payment_found = True
                break
    
    if not payment_found:
        raise HTTPException(
            status_code=402, 
            detail=f"No valid USDC transfer found. Required: ${required_amount_usd} USD ({required_usdc_units} units)"
        )

    USED_TRANSACTION_HASHES.add(x_payment_tx)
    return x_payment_tx