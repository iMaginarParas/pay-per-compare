import os
import replicate
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv

# 1. Load environment variables from .env file immediately
load_dotenv()

app = FastAPI(title="SDXL Image Generator API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"message": "SDXL Generator API is running."}

@app.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    # 2. Check for token availability before running
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        raise HTTPException(status_code=500, detail="REPLICATE_API_TOKEN is missing in .env file")

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
        
        # replicate.run automatically uses os.environ["REPLICATE_API_TOKEN"]
        output = replicate.run(
            model_version,
            input=input_data
        )

        image_urls = [str(item) for item in output]
        return ImageGenerationResponse(image_urls=image_urls)

    except replicate.exceptions.ReplicateError as e:
        raise HTTPException(status_code=502, detail=f"Replicate API Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)