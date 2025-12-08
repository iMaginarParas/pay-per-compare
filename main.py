import os
import replicate
from fastapi import FastAPI, HTTPException, Response, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
from web3 import Web3
from decimal import Decimal

# 1. Load environment variables
load_dotenv()

app = FastAPI(title="SDXL Image Generator API (Fuji Testnet)")

# --- CONFIGURATION FOR TESTNET ---
# Connect to Avalanche Fuji Testnet
AVAX_RPC_URL = "https://api.avax-test.network/ext/bc/C/rpc"
w3 = Web3(Web3.HTTPProvider(AVAX_RPC_URL))

# Load Wallet from .env
RECEIVING_WALLET_ADDRESS = os.getenv("RECEIVING_WALLET_ADDRESS") 

# Cost per generation (0.05 Testnet AVAX)
REQUIRED_AMOUNT_AVAX = Decimal("0.05") 

# In-memory storage to prevent Replay Attacks
USED_TRANSACTION_HASHES = set()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cost", "X-Run-Time"],
)

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: Optional[str] = Field(None, description="Things to avoid")
    width: int = Field(768, ge=128, le=1024)
    height: int = Field(768, ge=128, le=1024)
    num_inference_steps: int = Field(25, ge=1, le=50)
    refine: str = Field("expert_ensemble_refiner")
    apply_watermark: bool = Field(False)
    num_outputs: int = Field(1, ge=1, le=4)

class ImageGenerationResponse(BaseModel):
    image_urls: List[str]

@app.get("/")
async def root():
    return {
        "message": "SDXL Generator API (Testnet) is running.", 
        "payment_info": {
            "currency": "AVAX (Fuji Testnet)",
            "address": RECEIVING_WALLET_ADDRESS,
            "required_amount": float(REQUIRED_AMOUNT_AVAX)
        }
    }

async def verify_payment_middleware(x_payment_tx: str = Header(..., alias="X-Payment-Tx", description="The Transaction Hash")):
    """
    Verifies the transaction on the Avalanche Fuji Testnet.
    """
    if not RECEIVING_WALLET_ADDRESS:
        raise HTTPException(status_code=500, detail="Server misconfiguration: No wallet address set in .env")

    # 1. Check for Replay Attack
    if x_payment_tx in USED_TRANSACTION_HASHES:
        raise HTTPException(status_code=402, detail="Payment already used.")

    try:
        # 2. Fetch Transaction from Testnet
        tx = w3.eth.get_transaction(x_payment_tx)
        tx_receipt = w3.eth.get_transaction_receipt(x_payment_tx)
    except Exception:
        raise HTTPException(status_code=402, detail="Transaction hash not found on Avalanche Fuji Testnet.")

    # 3. Verify Status (1 = Success)
    if tx_receipt['status'] != 1:
        raise HTTPException(status_code=402, detail="Transaction failed on blockchain.")

    # 4. Verify Receiver
    if tx['to'].lower() != RECEIVING_WALLET_ADDRESS.lower():
        raise HTTPException(status_code=402, detail=f"Transaction sent to wrong address. Expected {RECEIVING_WALLET_ADDRESS}")

    # 5. Verify Amount
    value_in_avax = w3.from_wei(tx['value'], 'ether')
    if value_in_avax < REQUIRED_AMOUNT_AVAX:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient payment. Received {value_in_avax} AVAX, required {REQUIRED_AMOUNT_AVAX} AVAX."
        )

    # 6. Mark as used
    USED_TRANSACTION_HASHES.add(x_payment_tx)
    
    return x_payment_tx

@app.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest, 
    response: Response,
    payment_hash: str = Depends(verify_payment_middleware)
):
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        raise HTTPException(status_code=500, detail="REPLICATE_API_TOKEN is missing in .env")

    try:
        input_data = {
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "num_inference_steps": request.num_inference_steps,
            "refine": request.refine,
            "apply_watermark": request.apply_watermark,
            "num_outputs": request.num_outputs
        }
        
        if request.negative_prompt:
            input_data["negative_prompt"] = request.negative_prompt

        model_version = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"
        
        prediction = replicate.predictions.create(
            version=model_version,
            input=input_data
        )
        
        prediction.wait()
        
        if prediction.status != "succeeded":
            raise HTTPException(status_code=500, detail=f"Prediction failed: {prediction.error}")

        # Cost display for headers
        response.headers["X-Cost"] = "0.03 USD" 
        if prediction.metrics and "predict_time" in prediction.metrics:
            response.headers["X-Run-Time"] = str(prediction.metrics["predict_time"])

        output = prediction.output
        image_urls = [str(item) for item in output]
        
        return ImageGenerationResponse(image_urls=image_urls)

    except replicate.exceptions.ReplicateError as e:
        raise HTTPException(status_code=502, detail=f"Replicate API Error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)