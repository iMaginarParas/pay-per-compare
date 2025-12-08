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
from model.img2vid import (
    VideoGenerationRequest,
    VideoGenerationResponse,
    run_video_inference,
    VIDEO_MODEL_REGISTRY
)
from model.tts import (
    TTSRequest,
    TTSResponse,
    run_tts_inference,
    TTS_MODEL_REGISTRY,
    calculate_tts_cost
)

load_dotenv()

app = FastAPI(title="Multi-Model Image, Video & TTS Generator (USDC x402)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cost", "X-Run-Time"],
)

@app.get("/", tags=["Info"])
async def root():
    return {
        "message": "x402 Payment Gateway Running - Pay Per Use",
        "payment_info": {
            "currency": "USDC (Fuji)",
            "contract": USDC_CONTRACT_ADDRESS,
            "receiver": RECEIVING_WALLET_ADDRESS,
            "pricing": "Variable - depends on model selected",
            "image_models_range": "$0.0016 - $0.04 USD per generation",
            "video_models_range": "$0.05 - $0.08 USD per generation",
            "tts_models_range": "$0.01 - $0.06 USD per 1000 tokens"
        },
        "endpoints": {
            "list_image_models": "GET /models",
            "list_video_models": "GET /video-models",
            "list_tts_models": "GET /tts-models",
            "generate_image": "POST /generate",
            "generate_video": "POST /generate-video",
            "generate_tts": "POST /generate-tts"
        }
    }

@app.get("/models", tags=["Image Models"])
async def list_models():
    """List all available image models with their costs"""
    
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

@app.get("/video-models", tags=["Video Models"])
async def list_video_models():
    """List all available video models with their costs"""
    
    models_info = {}
    for model_name, config in VIDEO_MODEL_REGISTRY.items():
        models_info[model_name] = {
            "cost_usd": config["cost_usd"],
            "identifier": config.get("version") or config.get("identifier"),
            "type": config["type"]
        }
    
    return {
        "available_models": models_info,
        "total_models": len(models_info)
    }

@app.post("/generate", response_model=ImageGenerationResponse, tags=["Image Models"])
async def generate_image(
    request: ImageGenerationRequest, 
    response: Response,
    x_payment_tx: str = Header(..., alias="X-Payment-Tx")
):
    # Validate all selected models exist
    invalid_models = [m for m in request.models if m not in MODEL_REGISTRY]
    if invalid_models:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid models: {invalid_models}. Use GET /models to see available models."
        )
    
    # Calculate total cost for all selected models
    total_cost = sum(MODEL_REGISTRY[model]["cost_usd"] for model in request.models)
    
    # Verify payment with total cost
    await verify_usdc_payment(total_cost, x_payment_tx)
    
    # Run all models and get results
    generation_response = run_replicate_inference(request)
    
    return generation_response

@app.post("/generate-video", response_model=VideoGenerationResponse, tags=["Video Models"])
async def generate_video(
    request: VideoGenerationRequest,
    response: Response,
    x_payment_tx: str = Header(..., alias="X-Payment-Tx")
):
    # Validate all selected models exist
    invalid_models = [m for m in request.models if m not in VIDEO_MODEL_REGISTRY]
    if invalid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video models: {invalid_models}. Use GET /video-models to see available models."
        )
    
    # Calculate total cost for all selected models
    total_cost = sum(VIDEO_MODEL_REGISTRY[model]["cost_usd"] for model in request.models)
    
    # Verify payment with total cost
    await verify_usdc_payment(total_cost, x_payment_tx)
    
    # Run all models and get results
    generation_response = run_video_inference(request)
    
    return generation_response

@app.get("/tts-models", tags=["TTS Models"])
async def list_tts_models():
    """List all available TTS models with their costs"""
    
    models_info = {}
    for model_name, config in TTS_MODEL_REGISTRY.items():
        models_info[model_name] = {
            "cost_per_1000_tokens": config["cost_per_1000_tokens"],
            "identifier": config.get("version") or config.get("identifier"),
            "output_format": config["output_format"]
        }
    
    return {
        "available_models": models_info,
        "total_models": len(models_info),
        "note": "TTS models charge per 1000 input tokens. Approx 1 character = 1 token."
    }

@app.post("/generate-tts", response_model=TTSResponse, tags=["TTS Models"])
async def generate_tts(
    request: TTSRequest,
    response: Response,
    x_payment_tx: str = Header(..., alias="X-Payment-Tx")
):
    # Validate all selected models exist
    invalid_models = [m for m in request.models if m not in TTS_MODEL_REGISTRY]
    if invalid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid TTS models: {invalid_models}. Use GET /tts-models to see available models."
        )
    
    # Calculate total cost for all selected models based on text length
    total_cost = 0.0
    for model in request.models:
        cost, _ = calculate_tts_cost(model, request.text)
        total_cost += cost
    
    # Verify payment with total cost
    await verify_usdc_payment(total_cost, x_payment_tx)
    
    # Run all models and get results
    generation_response = run_tts_inference(request)
    
    return generation_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)