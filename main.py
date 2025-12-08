from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import logic from divided files
from x402.payment import (
    verify_usdc_payment, 
    USDC_CONTRACT_ADDRESS, 
    RECEIVING_WALLET_ADDRESS, 
    REQUIRED_USDC_AMOUNT
)
from model.txt2img import (
    ImageGenerationRequest, 
    ImageGenerationResponse, 
    run_replicate_inference
)

load_dotenv()

app = FastAPI(title="SDXL Generator (USDC x402)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cost", "X-Run-Time"],
)

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

@app.get("/models")
async def list_models():
    """List all available models with their costs"""
    from model.txt2img import MODEL_REGISTRY
    
    models_info = {}
    for model_name, config in MODEL_REGISTRY.items():
        models_info[model_name] = {
            "cost_usd": config["cost_usd"],
            "identifier": config.get("version") or config.get("identifier")
        }
    
    return {
        "available_models": models_info,
        "total_models": len(models_info)
    }

@app.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest, 
    response: Response,
    payment_hash: str = Depends(verify_usdc_payment)
):
    # The payment_hash dependency ensures payment is verified before this code runs.
    
    # Call the logic from model/txt2img.py
    image_urls = run_replicate_inference(request)
    
    # Get model cost from registry
    from model.txt2img import MODEL_REGISTRY
    model_cost = MODEL_REGISTRY[request.model]["cost_usd"]
    
    return ImageGenerationResponse(
        image_urls=image_urls,
        model_used=request.model,
        cost_usd=model_cost
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)