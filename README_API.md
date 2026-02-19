# Urdu Trigram Language Model API

FastAPI microservice for generating Urdu text using a trained trigram language model.

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure model files exist:**
   - `trigram_lm.pkl` (trained model)
   - `bpe_vocab.json` (tokenizer vocabulary)
   - `bpe_merges.txt` (BPE merge rules)

3. **Run the API server:**
   ```bash
   python api.py
   ```
   Or with uvicorn:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker

1. **Build the image:**
   ```bash
   docker build -t urdu-lm-api .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 urdu-lm-api
   ```

   Or with docker-compose:
   ```bash
   docker-compose up --build
   ```

## API Endpoints

### POST /generate

Generate text continuation from a prefix.

**Request Body:**
```json
{
  "prefix": "ایک جنگل میں",
  "max_length": 500,
  "temperature": 0.9,
  "random_seed": 42
}
```

**Response:**
```json
{
  "generated_text": "ایک جنگل میں ایک بڑا سا تالاب تھا...",
  "num_tokens": 150,
  "stopped_at_eot": true
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "tokenizer_loaded": true
}
```

### GET /

Root endpoint with service info.

## Example Usage

### Using curl:
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prefix": "ایک بار",
    "max_length": 200,
    "temperature": 0.9
  }'
```

### Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={
        "prefix": "ایک بار",
        "max_length": 200,
        "temperature": 0.9
    }
)

print(response.json()["generated_text"])
```

## Docker Deployment

The Dockerfile creates a production-ready container with:
- Python 3.11 slim base image
- Multi-stage build for smaller image size
- Health checks
- Optimized layer caching

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci-cd.yml`) includes:
- Automated testing
- Docker image building
- Container registry push (GitHub Container Registry)
- Deployment automation (configure your target)

## Environment Variables

- `PYTHONUNBUFFERED=1` - Recommended for Docker containers

## Notes

- Model files must exist before building the Docker image
- For production, consider using environment variables for model paths
- The API loads models at startup (cold start ~5-10 seconds)
- Health check endpoint helps with container orchestration
