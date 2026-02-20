"""
Phase IV: FastAPI Microservice for Trigram Language Model Inference
Exposes the trained model via REST API endpoint POST /generate
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
from pathlib import Path

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

app = FastAPI(
    title="Urdu Trigram Language Model API",
    description="REST API for generating Urdu text using a trigram language model",
    version="1.0.0",
)

# Enable CORS so the Next.js frontend (different origin) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for production, restrict this to your actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer (loaded at startup)
model = None
vocab = None
merge_rules = None


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


@app.on_event("startup")
async def load_models():
    """Load model and tokenizer at application startup."""
    global model, vocab, merge_rules
    
    print("Loading language model and tokenizer...")
    
    # Check if model files exist
    model_path = Path(MODEL_FILE)
    vocab_path = Path(VOCAB_FILE)
    merges_path = Path(MERGES_FILE)
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file '{MODEL_FILE}' not found. Run trigram_lm.py to train the model first."
        )
    if not vocab_path.exists() or not merges_path.exists():
        raise FileNotFoundError(
            f"Tokenizer files not found. Run train_bpe_tokenizer.py first."
        )
    
    # Load model and tokenizer
    model = load_model(MODEL_FILE)
    vocab, merge_rules = load_tokenizer(VOCAB_FILE, MERGES_FILE)
    
    print(f"✓ Model loaded: {len(model['unigram'])} unigrams, "
          f"{len(model['bigram'])} bigrams, {len(model['trigram'])} trigrams")
    print("✓ API ready to serve requests")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Urdu Trigram Language Model API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "tokenizer_loaded": vocab is not None
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text continuation from a given prefix.
    
    Args:
        request: GenerateRequest with prefix, max_length, temperature, and optional seed
        
    Returns:
        GenerateResponse with generated text, token count, and EOT flag
    """
    if model is None or vocab is None:
        raise HTTPException(
            status_code=503,
            detail="Model or tokenizer not loaded. Check server logs."
        )
    
    try:
        # Tokenize the prefix
        prefix_tokens = tokenize(request.prefix, vocab, merge_rules)
        
        # Use prefix as seed if provided, otherwise start from BOS
        if len(prefix_tokens) >= 2:
            seed_tokens = prefix_tokens[-2:]  # Use last 2 tokens for trigram context
        elif len(prefix_tokens) == 1:
            seed_tokens = [TOKEN_BOS, prefix_tokens[0]]
        else:
            seed_tokens = None  # Will use [BOS, BOS]
        
        # Generate tokens
        generated_tokens = generate(
            model=model,
            seed_tokens=seed_tokens,
            max_tokens=request.max_length,
            temperature=request.temperature,
            random_seed=request.random_seed,
        )
        
        # Remove BOS tokens and decode
        text_tokens = [t for t in generated_tokens if t != TOKEN_BOS]
        generated_text = decode(text_tokens)
        
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


if __name__ == "__main__":
    # Run with uvicorn for development
    uvicorn.run(app, host="0.0.0.0", port=8000)
