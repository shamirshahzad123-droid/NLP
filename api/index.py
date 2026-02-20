"""
Vercel Serverless Function for FastAPI Backend
This file handles all API routes for the Urdu Story Generator
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import sys
import re

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from trigram_lm import (
    load_model,
    load_tokenizer,
    tokenize,
    decode,
    generate,
    TOKEN_BOS,
    TOKEN_EOT,
    MODEL_FILE,
    VOCAB_FILE,
    MERGES_FILE,
)
from train_bpe_tokenizer import TOKEN_EOS, TOKEN_EOP

app = FastAPI(
    title="Urdu Trigram Language Model API",
    description="REST API for generating Urdu text using a trigram language model",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer (loaded lazily)
model = None
vocab = None
merge_rules = None


def get_model():
    """Lazy load model - Vercel serverless functions need this pattern"""
    global model, vocab, merge_rules
    
    if model is None or vocab is None:
        print("Loading language model and tokenizer...")
        
        model_path = Path(MODEL_FILE)
        vocab_path = Path(VOCAB_FILE)
        merges_path = Path(MERGES_FILE)
        
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file '{MODEL_FILE}' not found."
            )
        if not vocab_path.exists() or not merges_path.exists():
            raise FileNotFoundError(
                f"Tokenizer files not found."
            )
        
        model = load_model(MODEL_FILE)
        vocab, merge_rules = load_tokenizer(VOCAB_FILE, MERGES_FILE)
        
        print(f"✓ Model loaded: {len(model['unigram'])} unigrams, "
              f"{len(model['bigram'])} bigrams, {len(model['trigram'])} trigrams")
    
    return model, vocab, merge_rules


class GenerateRequest(BaseModel):
    """Request model for text generation."""
    prefix: str = Field(..., description="Input prefix text to continue from")
    max_length: int = Field(
        default=500,
        ge=1,
        le=2000,
        description="Maximum number of tokens to generate (1-2000)"
    )
    temperature: Optional[float] = Field(
        default=0.9,
        ge=0.1,
        le=2.0,
        description="Sampling temperature (0.1-2.0, lower = more deterministic)"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility (optional)"
    )


class GenerateResponse(BaseModel):
    """Response model for generated text."""
    generated_text: str = Field(..., description="Generated text continuation")
    num_tokens: int = Field(..., description="Number of tokens generated")
    stopped_at_eot: bool = Field(..., description="Whether generation stopped at EOT token")


# Routes - handle both with and without /api prefix to cover different Vercel rewrite behaviors
@app.get("/")
@app.get("/api")
@app.get("/api/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Urdu Trigram Language Model API",
        "version": "1.0.0"
    }


@app.get("/health")
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    try:
        model, vocab, _ = get_model()
        return {
            "status": "healthy",
            "model_loaded": model is not None,
            "tokenizer_loaded": vocab is not None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Handle OPTIONS for CORS preflight
@app.options("/generate")
@app.options("/api/generate")
async def options_generate():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
@app.post("/api/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text continuation from a given prefix.
    """
    try:
        model, vocab, merge_rules = get_model()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Model loading error: {str(e)}"
        )
    
    try:
        # Tokenize the prefix
        prefix_tokens = tokenize(request.prefix, vocab, merge_rules)
        
        # Use prefix as seed if provided, otherwise start from BOS
        if len(prefix_tokens) >= 2:
            seed_tokens = prefix_tokens[-2:]
        elif len(prefix_tokens) == 1:
            seed_tokens = [TOKEN_BOS, prefix_tokens[0]]
        else:
            seed_tokens = None
        
        # Generate tokens
        generated_tokens = generate(
            model=model,
            seed_tokens=seed_tokens,
            max_tokens=request.max_length,
            temperature=request.temperature,
            random_seed=request.random_seed,
        )
        
        # Remove special tokens (BOS, EOS, EOP, EOT) and decode
        special_tokens = {TOKEN_BOS, TOKEN_EOS, TOKEN_EOP, TOKEN_EOT}
        text_tokens = [t for t in generated_tokens if t not in special_tokens]
        generated_text = decode(text_tokens)
        
        # Clean up any remaining special token characters
        generated_text = generated_text.replace(TOKEN_EOS, "۔")
        generated_text = generated_text.replace(TOKEN_EOP, "\n\n")
        generated_text = generated_text.replace(TOKEN_EOT, "")
        generated_text = generated_text.replace(TOKEN_BOS, "")
        
        # Clean up multiple spaces and normalize whitespace
        generated_text = re.sub(r'\s+', ' ', generated_text)
        generated_text = generated_text.strip()
        
        # Check if stopped at EOT
        stopped_at_eot = TOKEN_EOT in generated_tokens
        
        return GenerateResponse(
            generated_text=generated_text,
            num_tokens=len(text_tokens),
            stopped_at_eot=stopped_at_eot
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during generation: {str(e)}"
        )


# Vercel serverless function handler
from mangum import Mangum

# Export handler for Vercel - Mangum converts FastAPI ASGI app to AWS Lambda/Vercel format
# Routes handle both /generate and /api/generate to cover different Vercel rewrite behaviors
handler = Mangum(app, lifespan="off")

# For local testing (not used in Vercel)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
