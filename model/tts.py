import os
import replicate
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

# TTS Model Registry with pricing and configuration
TTS_MODEL_REGISTRY = {
    "minimax-speech-turbo": {
        "identifier": "minimax/speech-02-turbo",
        "cost_per_1000_tokens": 0.06,
        "output_type": "single",
        "output_format": "mp3"
    },
    "chatterbox": {
        "identifier": "resemble-ai/chatterbox",
        "cost_per_1000_tokens": 0.025,
        "output_type": "single",
        "output_format": "wav"
    },
    "kokoro-82m": {
        "version": "jaaari/kokoro-82m:f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13",
        "cost_per_1000_tokens": 0.01,
        "output_type": "single",
        "output_format": "wav"
    }
}

class TTSRequest(BaseModel):
    text: str  # Text to convert to speech
    models: List[str] = ["kokoro-82m"]  # Default to cheapest model
    
    # Optional parameters for different TTS models
    voice: Optional[str] = None  # Voice ID/name (kokoro: "af_nicole", minimax: "Deep_Voice_Man")
    voice_id: Optional[str] = None  # For minimax
    emotion: Optional[str] = None  # For minimax: "neutral", "happy", "sad", "angry", etc.
    language_boost: Optional[str] = None  # For minimax: "English", "Spanish", etc.
    english_normalization: Optional[bool] = None  # For minimax
    prompt: Optional[str] = None  # For chatterbox (uses 'prompt' instead of 'text')

class TTSResult(BaseModel):
    model_name: str
    audio_urls: List[str]
    cost_usd: float
    tokens_used: int
    status: str  # "success" or "error"
    error_message: Optional[str] = None

class TTSResponse(BaseModel):
    results: List[TTSResult]
    total_cost_usd: float
    total_models: int
    successful: int
    failed: int
    total_tokens: int

def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    For TTS models, typically 1 character ≈ 1 token.
    """
    return len(text)

def calculate_tts_cost(model_name: str, text: str) -> tuple:
    """
    Calculate cost for TTS generation based on token count.
    Returns (cost_usd, token_count)
    """
    if model_name not in TTS_MODEL_REGISTRY:
        return (0.0, 0)
    
    model_config = TTS_MODEL_REGISTRY[model_name]
    token_count = estimate_tokens(text)
    cost = (token_count / 1000) * model_config["cost_per_1000_tokens"]
    
    return (cost, token_count)

def run_single_tts_inference(model_name: str, request: TTSRequest) -> TTSResult:
    """
    Run inference for a single TTS model.
    Returns TTSResult with success/error status.
    """
    try:
        # Validate model selection
        if model_name not in TTS_MODEL_REGISTRY:
            return TTSResult(
                model_name=model_name,
                audio_urls=[],
                cost_usd=0.0,
                tokens_used=0,
                status="error",
                error_message=f"TTS model '{model_name}' not found"
            )
        
        model_config = TTS_MODEL_REGISTRY[model_name]
        
        # Calculate cost based on text length
        cost, tokens = calculate_tts_cost(model_name, request.text)
        
        # Build input data based on model requirements
        input_data = {}
        
        # Different models use different field names
        if model_name == "chatterbox":
            # Chatterbox uses 'prompt' field
            input_data["prompt"] = request.prompt if request.prompt else request.text
        else:
            # Most models use 'text' field
            input_data["text"] = request.text
        
        # Add optional parameters for minimax
        if model_name == "minimax-speech-turbo":
            if request.voice_id:
                input_data["voice_id"] = request.voice_id
            if request.emotion:
                input_data["emotion"] = request.emotion
            if request.language_boost:
                input_data["language_boost"] = request.language_boost
            if request.english_normalization is not None:
                input_data["english_normalization"] = request.english_normalization
        
        # Add voice parameter for kokoro
        if model_name == "kokoro-82m" and request.voice:
            input_data["voice"] = request.voice
        
        # Determine which identifier to use
        model_ref = model_config.get("version") or model_config.get("identifier")
        
        # Run the model
        output = replicate.run(model_ref, input=input_data)
        
        # Handle output (always single audio file for TTS)
        if isinstance(output, str):
            audio_urls = [output]
        elif hasattr(output, 'url'):
            url_attr = getattr(output, 'url')
            if callable(url_attr):
                audio_urls = [str(url_attr())]
            else:
                audio_urls = [str(url_attr)]
        else:
            audio_urls = [str(output)]
        
        return TTSResult(
            model_name=model_name,
            audio_urls=audio_urls,
            cost_usd=cost,
            tokens_used=tokens,
            status="success"
        )
        
    except Exception as e:
        # Return error result if model fails
        cost, tokens = calculate_tts_cost(model_name, request.text)
        return TTSResult(
            model_name=model_name,
            audio_urls=[],
            cost_usd=cost,
            tokens_used=tokens,
            status="error",
            error_message=str(e)
        )

def run_tts_inference(request: TTSRequest) -> TTSResponse:
    """
    Handles calls to Replicate with multiple TTS model support.
    Runs all selected models and returns combined results.
    """
    results = []
    
    # Run each model
    for model_name in request.models:
        result = run_single_tts_inference(model_name, request)
        results.append(result)
    
    # Calculate totals
    total_cost = sum(r.cost_usd for r in results)
    total_tokens = sum(r.tokens_used for r in results)
    successful = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "error")
    
    return TTSResponse(
        results=results,
        total_cost_usd=total_cost,
        total_models=len(results),
        successful=successful,
        failed=failed,
        total_tokens=total_tokens
    )