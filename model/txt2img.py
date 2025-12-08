import os
import replicate
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 768
    height: int = 768
    num_inference_steps: int = 25

class ImageGenerationResponse(BaseModel):
    image_urls: List[str]

def run_replicate_inference(request: ImageGenerationRequest) -> List[str]:
    """
    Handles the call to Replicate SDXL.
    """
    # Ensure REPLICATE_API_TOKEN is set in env
    input_data = {
        "prompt": request.prompt,
        "width": request.width,
        "height": request.height,
        "num_inference_steps": request.num_inference_steps
    }
    
    # Add negative prompt if it exists
    if request.negative_prompt:
        input_data["negative_prompt"] = request.negative_prompt

    prediction = replicate.predictions.create(
        version="stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
        input=input_data
    )
    prediction.wait()
    
    # Ensure we return a list of strings
    return [str(url) for url in prediction.output]