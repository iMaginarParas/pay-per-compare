import os
import replicate
from pydantic import BaseModel
from typing import Optional, List, Any
from dotenv import load_dotenv

load_dotenv()

# Model Registry with pricing and configuration
MODEL_REGISTRY = {
    "sdxl": {
        "version": "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
        "cost_usd": 0.03,
        "output_type": "array"
    },
    "luma-photon": {
        "identifier": "luma/photon",
        "cost_usd": 0.03,
        "output_type": "single"
    },
    "sdxl-lightning": {
        "version": "bytedance/sdxl-lightning-4step:6f7a773af6fc3e8de9d5a3c00be77c17308914bf67772726aff83496ba1e3bbe",
        "cost_usd": 0.0016,
        "output_type": "array"
    },
    "luma-photon-flash": {
        "identifier": "luma/photon-flash",
        "cost_usd": 0.01,
        "output_type": "single"
    },
    "minimax-image-01": {
        "identifier": "minimax/image-01",
        "cost_usd": 0.01,
        "output_type": "array"
    },
    "ideogram-v2-turbo": {
        "identifier": "ideogram-ai/ideogram-v2a-turbo",
        "cost_usd": 0.025,
        "output_type": "single"
    },
    "recraft-v3": {
        "identifier": "recraft-ai/recraft-v3",
        "cost_usd": 0.04,
        "output_type": "single"
    },
    "phoenix-1.0": {
        "identifier": "leonardoai/phoenix-1.0",
        "cost_usd": 0.002,
        "output_type": "array"
    },
    "flux-fast": {
        "identifier": "prunaai/flux-fast",
        "cost_usd": 0.005,
        "output_type": "single"
    },
    "seedream-3": {
        "identifier": "bytedance/seedream-3",
        "cost_usd": 0.03,
        "output_type": "single"
    },
    "flux-kontext-pro": {
        "identifier": "black-forest-labs/flux-kontext-pro",
        "cost_usd": 0.04,
        "output_type": "single"
    },
    "imagen-3-fast": {
        "identifier": "google/imagen-3-fast",
        "cost_usd": 0.025,
        "output_type": "single"
    },
    "nano-banana": {
        "identifier": "google/nano-banana",
        "cost_usd": 0.039,
        "output_type": "single"
    },
    "flux-schnell": {
        "identifier": "black-forest-labs/flux-schnell",
        "cost_usd": 0.003,
        "output_type": "array"
    },
    "ideogram-v3-turbo": {
        "identifier": "ideogram-ai/ideogram-v3-turbo",
        "cost_usd": 0.03,
        "output_type": "single"
    },
    "seedream-4": {
        "identifier": "bytedance/seedream-4",
        "cost_usd": 0.03,
        "output_type": "array"
    },
    "imagen-4-fast": {
        "identifier": "google/imagen-4-fast",
        "cost_usd": 0.02,
        "output_type": "single"
    }
}

class ImageGenerationRequest(BaseModel):
    prompt: str
    models: List[str] = ["sdxl"]  # Can select multiple models now!
    
    # Optional parameters that different models might use
    negative_prompt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None  # e.g., "16:9", "3:2", "4:3"
    size: Optional[str] = None  # e.g., "1365x1024" for recraft
    num_inference_steps: Optional[int] = None
    style: Optional[str] = None  # For models like phoenix-1.0
    safety_filter_level: Optional[str] = None  # For imagen models
    output_format: Optional[str] = None  # jpg, png, webp
    input_image: Optional[str] = None  # For image-to-image models
    image_input: Optional[List[str]] = None  # For multi-image input models

class ModelResult(BaseModel):
    model_name: str
    image_urls: List[str]
    cost_usd: float
    status: str  # "success" or "error"
    error_message: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    results: List[ModelResult]
    total_cost_usd: float
    total_models: int
    successful: int
    failed: int

def run_single_model_inference(model_name: str, request: ImageGenerationRequest) -> ModelResult:
    """
    Run inference for a single model.
    Returns ModelResult with success/error status.
    """
    try:
        # Validate model selection
        if model_name not in MODEL_REGISTRY:
            return ModelResult(
                model_name=model_name,
                image_urls=[],
                cost_usd=0.0,
                status="error",
                error_message=f"Model '{model_name}' not found"
            )
        
        model_config = MODEL_REGISTRY[model_name]
        
        # Build input data based on what's provided
        input_data = {"prompt": request.prompt}
        
        # Add optional parameters if they exist
        if request.negative_prompt:
            input_data["negative_prompt"] = request.negative_prompt
        
        if request.width:
            input_data["width"] = request.width
        
        if request.height:
            input_data["height"] = request.height
        
        if request.aspect_ratio:
            input_data["aspect_ratio"] = request.aspect_ratio
        
        if request.size:
            input_data["size"] = request.size
        
        if request.num_inference_steps:
            input_data["num_inference_steps"] = request.num_inference_steps
        
        if request.style:
            input_data["style"] = request.style
        
        if request.safety_filter_level:
            input_data["safety_filter_level"] = request.safety_filter_level
        
        if request.output_format:
            input_data["output_format"] = request.output_format
        
        if request.input_image:
            input_data["input_image"] = request.input_image
        
        if request.image_input:
            input_data["image_input"] = request.image_input
        
        # Determine which identifier to use (version or identifier)
        model_ref = model_config.get("version") or model_config.get("identifier")
        
        # Run the model
        output = replicate.run(model_ref, input=input_data)
        
        # Handle different output types
        if model_config["output_type"] == "single":
            # Single output - handle all possible formats
            if isinstance(output, str):
                image_urls = [output]
            elif hasattr(output, 'url'):
                url_attr = getattr(output, 'url')
                if callable(url_attr):
                    image_urls = [str(url_attr())]
                else:
                    image_urls = [str(url_attr)]
            else:
                image_urls = [str(output)]
        else:
            # Array output - handle each item
            image_urls = []
            for item in output:
                if isinstance(item, str):
                    image_urls.append(item)
                elif hasattr(item, 'url'):
                    url_attr = getattr(item, 'url')
                    if callable(url_attr):
                        image_urls.append(str(url_attr()))
                    else:
                        image_urls.append(str(url_attr))
                else:
                    image_urls.append(str(item))
        
        return ModelResult(
            model_name=model_name,
            image_urls=image_urls,
            cost_usd=model_config["cost_usd"],
            status="success"
        )
        
    except Exception as e:
        # Return error result if model fails
        model_cost = MODEL_REGISTRY.get(model_name, {}).get("cost_usd", 0.0)
        return ModelResult(
            model_name=model_name,
            image_urls=[],
            cost_usd=model_cost,
            status="error",
            error_message=str(e)
        )

def run_replicate_inference(request: ImageGenerationRequest) -> ImageGenerationResponse:
    """
    Handles calls to Replicate with multiple model support.
    Runs all selected models and returns combined results.
    """
    results = []
    
    # Run each model
    for model_name in request.models:
        result = run_single_model_inference(model_name, request)
        results.append(result)
    
    # Calculate totals
    total_cost = sum(r.cost_usd for r in results)
    successful = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "error")
    
    return ImageGenerationResponse(
        results=results,
        total_cost_usd=total_cost,
        total_models=len(results),
        successful=successful,
        failed=failed
    )