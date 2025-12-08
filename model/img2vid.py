import os
import replicate
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

# Video Model Registry with pricing and configuration
VIDEO_MODEL_REGISTRY = {
    "wan-i2v-fast": {
        "identifier": "wan-video/wan-2.2-i2v-fast",
        "cost_usd": 0.05,
        "output_type": "single",
        "type": "image-to-video"
    },
    "ltx-video": {
        "version": "lightricks/ltx-video:8c47da666861d081eeb4d1261853087de23923a268a69b63febdf5dc1dee08e4",
        "cost_usd": 0.08,
        "output_type": "array",
        "type": "text-to-video"
    }
}

class VideoGenerationRequest(BaseModel):
    prompt: str
    models: List[str] = ["ltx-video"]  # Default to text-to-video model
    
    # Optional parameters for video generation
    image: Optional[str] = None  # For image-to-video models (URL)
    aspect_ratio: Optional[str] = None  # e.g., "16:9", "9:16"
    negative_prompt: Optional[str] = None
    duration: Optional[int] = None  # Video duration in seconds
    fps: Optional[int] = None  # Frames per second
    motion_bucket_id: Optional[int] = None  # Motion strength

class VideoResult(BaseModel):
    model_name: str
    video_urls: List[str]
    cost_usd: float
    status: str  # "success" or "error"
    error_message: Optional[str] = None

class VideoGenerationResponse(BaseModel):
    results: List[VideoResult]
    total_cost_usd: float
    total_models: int
    successful: int
    failed: int

def run_single_video_model_inference(model_name: str, request: VideoGenerationRequest) -> VideoResult:
    """
    Run inference for a single video model.
    Returns VideoResult with success/error status.
    """
    try:
        # Validate model selection
        if model_name not in VIDEO_MODEL_REGISTRY:
            return VideoResult(
                model_name=model_name,
                video_urls=[],
                cost_usd=0.0,
                status="error",
                error_message=f"Video model '{model_name}' not found"
            )
        
        model_config = VIDEO_MODEL_REGISTRY[model_name]
        
        # Build input data based on what's provided
        input_data = {"prompt": request.prompt}
        
        # Add image for image-to-video models
        if request.image and model_config["type"] == "image-to-video":
            input_data["image"] = request.image
        
        # Add optional parameters if they exist
        if request.aspect_ratio:
            input_data["aspect_ratio"] = request.aspect_ratio
        
        if request.negative_prompt:
            input_data["negative_prompt"] = request.negative_prompt
        
        if request.duration:
            input_data["duration"] = request.duration
        
        if request.fps:
            input_data["fps"] = request.fps
        
        if request.motion_bucket_id:
            input_data["motion_bucket_id"] = request.motion_bucket_id
        
        # Determine which identifier to use
        model_ref = model_config.get("version") or model_config.get("identifier")
        
        # Run the model
        output = replicate.run(model_ref, input=input_data)
        
        # Handle different output types
        if model_config["output_type"] == "single":
            # Single output
            if isinstance(output, str):
                video_urls = [output]
            elif hasattr(output, 'url'):
                url_attr = getattr(output, 'url')
                if callable(url_attr):
                    video_urls = [str(url_attr())]
                else:
                    video_urls = [str(url_attr)]
            else:
                video_urls = [str(output)]
        else:
            # Array output
            video_urls = []
            for item in output:
                if isinstance(item, str):
                    video_urls.append(item)
                elif hasattr(item, 'url'):
                    url_attr = getattr(item, 'url')
                    if callable(url_attr):
                        video_urls.append(str(url_attr()))
                    else:
                        video_urls.append(str(url_attr))
                else:
                    video_urls.append(str(item))
        
        return VideoResult(
            model_name=model_name,
            video_urls=video_urls,
            cost_usd=model_config["cost_usd"],
            status="success"
        )
        
    except Exception as e:
        # Return error result if model fails
        model_cost = VIDEO_MODEL_REGISTRY.get(model_name, {}).get("cost_usd", 0.0)
        return VideoResult(
            model_name=model_name,
            video_urls=[],
            cost_usd=model_cost,
            status="error",
            error_message=str(e)
        )

def run_video_inference(request: VideoGenerationRequest) -> VideoGenerationResponse:
    """
    Handles calls to Replicate with multiple video model support.
    Runs all selected models and returns combined results.
    """
    results = []
    
    # Run each model
    for model_name in request.models:
        result = run_single_video_model_inference(model_name, request)
        results.append(result)
    
    # Calculate totals
    total_cost = sum(r.cost_usd for r in results)
    successful = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "error")
    
    return VideoGenerationResponse(
        results=results,
        total_cost_usd=total_cost,
        total_models=len(results),
        successful=successful,
        failed=failed
    )