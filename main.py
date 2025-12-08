import os
import replicate
from fastapi import FastAPI, HTTPException, Response, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
from web3 import Web3
from eth_utils import to_checksum_address

load_dotenv()

app = FastAPI(title="SDXL Generator (USDC x402)")

# --- CONFIGURATION ---
# Connect to Fuji Testnet
AVAX_RPC_URL = "https://api.avax-test.network/ext/bc/C/rpc"
w3 = Web3(Web3.HTTPProvider(AVAX_RPC_URL))

RECEIVING_WALLET_ADDRESS = to_checksum_address(os.getenv("RECEIVING_WALLET_ADDRESS"))
USDC_CONTRACT_ADDRESS = to_checksum_address(os.getenv("USDC_CONTRACT_ADDRESS"))

# Cost: 1.0 USDC (USDC has 6 decimals, so 1.0 = 1,000,000 units)
REQUIRED_USDC_AMOUNT = int(0.03 * 10**6)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cost", "X-Run-Time"],
)

class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 768
    height: int = 768
    num_inference_steps: int = 25

class ImageGenerationResponse(BaseModel):
    image_urls: List[str]

@app.get("/")
async def root():
    return {
        "message": "x402 Payment Gateway Running",
        "payment_info": {
            "currency": "USDC (Fuji)",
            "contract": USDC_CONTRACT_ADDRESS,
            "receiver": RECEIVING_WALLET_ADDRESS,
            "amount_units": REQUIRED_USDC_AMOUNT,
            "readable_amount": "0.03 USDC"
        }
    }

async def verify_usdc_payment(x_payment_tx: str = Header(..., alias="X-Payment-Tx")):
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
            if transfer['args']['value'] >= REQUIRED_USDC_AMOUNT:
                payment_found = True
                break
    
    if not payment_found:
        raise HTTPException(status_code=402, detail="No valid USDC transfer found in this transaction.")

    USED_TRANSACTION_HASHES.add(x_payment_tx)
    return x_payment_tx

@app.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest, 
    response: Response,
    payment_hash: str = Depends(verify_usdc_payment)
):
    # ... (Your existing Replicate generation code here) ...
    # This part is identical to your previous code
    
    api_token = os.getenv("REPLICATE_API_TOKEN")
    input_data = {
        "prompt": request.prompt,
        "width": request.width,
        "height": request.height,
        "num_inference_steps": request.num_inference_steps
    }
    
    prediction = replicate.predictions.create(
        version="stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
        input=input_data
    )
    prediction.wait()
    return ImageGenerationResponse(image_urls=[str(url) for url in prediction.output])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)