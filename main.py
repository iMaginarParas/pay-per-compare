from fastapi import FastAPI, Response, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import logic from divided files
from x402.payment import (
    verify_usdc_payment, 
    USDC_CONTRACT_ADDRESS, 
    RECEIVING_WALLET_ADDRESS
)
from model.txt2img import (
    ImageGenerationRequest, 
    ImageGenerationResponse, 
    run_replicate_inference,
    MODEL_REGISTRY
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
        "message": "x402 Payment Gateway Running - Pay Per Use",
        "payment_info": {
            "currency": "USDC (Fuji)",
            "contract": USDC_CONTRACT_ADDRESS,
            "receiver": RECEIVING_WALLET_ADDRESS,
            "pricing": "Variable - depends on model selected",
            "range": "$0.0016 - $0.04 USD per generation"
        },
        "endpoints": {
            "list_models": "GET /models",
            "generate": "POST /generate"
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
    x_payment_tx: str = Header(..., alias="X-Payment-Tx")
):
    # Validate model exists
    if request.model not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=400, 
            detail=f"Model '{request.model}' not found. Use GET /models to see available models."
        )
    
    # Get model cost
    model_cost = MODEL_REGISTRY[request.model]["cost_usd"]
    
    # Verify payment with the model's actual cost
    await verify_usdc_payment(model_cost, x_payment_tx)
    
    # Call the logic from model/txt2img.py
    image_urls = run_replicate_inference(request)
    
    return ImageGenerationResponse(
        image_urls=image_urls,
        model_used=request.model,
        cost_usd=model_cost
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)