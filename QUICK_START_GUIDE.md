# 🚀 Complete Step-by-Step Guide

## 📋 Prerequisites Check

First, verify you have Python 3.11+ installed:
```bash
python --version
```

---

## 🔍 Step 1: Check What You Already Have

Check if you already have the required files:

```bash
# Check for model files
dir trigram_lm.pkl
dir bpe_vocab.json
dir bpe_merges.txt
dir urdu_stories_preprocessed.txt

# Check for data folder
dir data
```

**If you see all these files, skip to Step 4 (API).**

---

## 📊 Phase I: Data Scraping (If Needed)

**Only run if you don't have the `data/` folder with 200 stories.**

```bash
# Install scraping dependencies
pip install selenium beautifulsoup4 requests webdriver-manager

# Run scraper
python scrape.py
```

⏱️ **Time:** ~30-60 minutes (scrapes 200 stories)

**Expected output:** `data/` folder with 200 `.txt` files

---

## 🧹 Phase II: Preprocessing (If Needed)

**Only run if you don't have `urdu_stories_preprocessed.txt`.**

```bash
# Run preprocessing
python preprocess.py
```

⏱️ **Time:** ~1-2 minutes

**Expected output:** `urdu_stories_preprocessed.txt`

---

## 🔤 Phase III: BPE Tokenizer Training (If Needed)

**Only run if you don't have `bpe_vocab.json` and `bpe_merges.txt`.**

```bash
# Run tokenizer training
python train_bpe_tokenizer.py
```

⏱️ **Time:** ~2-3 minutes

**Expected output:** 
- `bpe_vocab.json`
- `bpe_merges.txt`

---

## 🧠 Phase IV: Language Model Training (If Needed)

**Only run if you don't have `trigram_lm.pkl`.**

```bash
# Run LM training
python trigram_lm.py
```

⏱️ **Time:** ~5-10 minutes (first run), ~30 seconds (with cache)

**Expected output:**
- `trigram_lm.pkl` (main model file)
- `trigram_lm.json` (backup)
- `corpus_tokens_cache.json` (for faster reruns)

---

## 🌐 Phase V: Run the API Server

### Option A: Run Locally (Recommended for Testing)

**Step 1: Install API dependencies (use venv-1 if pip install fails globally)**
```bash
# Option A: Global install
pip install -r requirements.txt

# Option B: Using venv-1 (if Option A fails)
.\venv-1\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Step 2: Start the API server**
```bash
# If using venv-1, activate first:
.\venv-1\Scripts\Activate.ps1

python api.py
```

You should see:
```
Loading language model and tokenizer...
✓ Model loaded: 226 unigrams, 3073 bigrams, 12271 trigrams
✓ API ready to serve requests
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Step 3: Test the API (in a NEW terminal)**

Open a **new terminal window** and run:
```bash
# Test health endpoint
curl http://localhost:8000/health

# Or use the test script
python test_api.py
```

**Step 4: Access API Documentation**

Open your browser:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

**Step 5: Test Generation**

Using curl:
```bash
curl -X POST "http://localhost:8000/generate" ^
  -H "Content-Type: application/json" ^
  -d "{\"prefix\": \"ایک بار\", \"max_length\": 200, \"temperature\": 0.9}"
```

Or using Python:
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

---

### Option B: Run with Docker

**Step 1: Build Docker Image**
```bash
docker build -t urdu-lm-api .
```

⏱️ **Time:** ~2-3 minutes (first build)

**Step 2: Run Container**
```bash
docker run -p 8000:8000 urdu-lm-api
```

**Or use docker-compose (easier):**
```bash
docker-compose up --build
```

**Step 3: Test (same as Option A)**
```bash
curl http://localhost:8000/health
python test_api.py
```

---

## 🧪 Quick Test Checklist

Run these commands to verify everything works:

```bash
# 1. Check all required files exist
python -c "import os; files=['trigram_lm.pkl','bpe_vocab.json','bpe_merges.txt']; print('✓' if all(os.path.exists(f) for f in files) else '✗ Missing files')"

# 2. Test model loading
python -c "from trigram_lm import load_model; m=load_model('trigram_lm.pkl'); print(f'✓ Model loaded: {len(m[\"unigram\"])} unigrams')"

# 3. Test API (if running)
curl http://localhost:8000/health
```

---

## 📝 Complete Workflow Summary

**If starting from scratch:**

```bash
# 1. Scrape data
python scrape.py

# 2. Preprocess
python preprocess.py

# 3. Train tokenizer
python train_bpe_tokenizer.py

# 4. Train language model
python trigram_lm.py

# 5. Install API dependencies
pip install -r requirements.txt

# 6. Run API
python api.py

# 7. Test (in new terminal)
python test_api.py
```

**If you already have model files:**

```bash
# 1. Install API dependencies
pip install -r requirements.txt

# 2. Run API
python api.py

# 3. Test
python test_api.py
```

---

## 🐛 Troubleshooting

### Error: "Model file not found"
**Solution:** Run `python trigram_lm.py` first to train the model.

### Error: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:** Run `pip install -r requirements.txt`

### Error: "Port 8000 already in use"
**Solution:** 
- Change port in `api.py`: `uvicorn.run(app, host="0.0.0.0", port=8001)`
- Or kill the process: `netstat -ano | findstr :8000` then `taskkill /PID <pid> /F`

### Docker build fails: "Model file not found"
**Solution:** Make sure `trigram_lm.pkl`, `bpe_vocab.json`, and `bpe_merges.txt` exist before building.

### API takes long to start
**Normal!** Model loading takes 5-10 seconds. Wait for "✓ API ready to serve requests"

---

## 🎯 What to Do Right Now

**Based on your current files, you likely need to:**

1. **Install API dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server:**
   ```bash
   python api.py
   ```

3. **Test it (in a new terminal):**
   ```bash
   python test_api.py
   ```

4. **Open browser to see API docs:**
   - Go to: http://localhost:8000/docs

---

## 📚 Next Steps

- **Test the API** using the Swagger UI at http://localhost:8000/docs
- **Try different prefixes** and see what the model generates
- **Deploy to production** using Docker or cloud services
- **Set up CI/CD** by pushing to GitHub (the workflow is already configured)

---

## 💡 Pro Tips

1. **Keep the API running** in one terminal, use another for testing
2. **Use Swagger UI** (http://localhost:8000/docs) - it's interactive!
3. **Adjust temperature** (0.1-2.0) to control randomness
4. **Use random_seed** for reproducible results
5. **Check logs** if something fails - the API prints helpful messages

---

**Need help?** Check the error messages - they usually tell you what's missing!
