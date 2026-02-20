# 🚀 Complete Vercel Deployment Guide

Deploy both **Frontend (Next.js)** and **Backend (FastAPI)** on Vercel in one project.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code should be pushed to GitHub
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com) (free tier available)
3. **Git installed** on your machine

---

## 🎯 Project Structure

```
NLP/
├── frontend/          # Next.js frontend
│   ├── app/
│   ├── package.json
│   └── ...
├── api/              # FastAPI backend (Vercel serverless functions)
│   └── index.py
├── vercel.json       # Vercel configuration
├── requirements.txt  # Python dependencies
├── trigram_lm.py
├── train_bpe_tokenizer.py
├── trigram_lm.pkl    # Model files (must be in repo)
├── bpe_vocab.json
└── bpe_merges.txt
```

---

## 📦 Step-by-Step Deployment

### Step 1: Prepare Your Code

1. **Ensure all files are committed:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Verify these files exist:**
   - ✅ `vercel.json` (root directory)
   - ✅ `api/index.py` (Vercel serverless function)
   - ✅ `frontend/package.json`
   - ✅ `requirements.txt`
   - ✅ Model files: `trigram_lm.pkl`, `bpe_vocab.json`, `bpe_merges.txt`

### Step 2: Deploy on Vercel

1. **Go to [vercel.com](https://vercel.com)** and sign in

2. **Click "Add New..." → "Project"**

3. **Import your GitHub repository:**
   - Select your `NLP` repository
   - Click "Import"

4. **Configure Project Settings:**

   **Framework Preset:** Next.js (auto-detected)
   
   **Root Directory:** Leave empty (root of repo)
   
   **Build and Output Settings:**
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/.next`
   - Install Command: `cd frontend && npm install`

   **OR use the simpler approach:**
   - Root Directory: `frontend`
   - Vercel will auto-detect Next.js

5. **Environment Variables:**
   - No need to set `NEXT_PUBLIC_API_BASE_URL` - the frontend will automatically use `/api` when deployed on Vercel

6. **Python Settings:**
   - Vercel will automatically detect Python from `requirements.txt`
   - The `api/` directory will be treated as serverless functions

7. **Click "Deploy"**

8. **Wait for deployment** (5-10 minutes):
   - Frontend builds first
   - Then Python functions are set up
   - Model files are uploaded

### Step 3: Verify Deployment

1. **Check deployment logs:**
   - Look for "Build successful"
   - Check for any Python errors

2. **Test the API:**
   ```
   https://your-project.vercel.app/api/health
   ```
   Should return:
   ```json
   {"status":"healthy","model_loaded":true,"tokenizer_loaded":true}
   ```

3. **Test the frontend:**
   - Open `https://your-project.vercel.app`
   - Enter an Urdu phrase like `ایک بار`
   - Click "کہانی مکمل کریں"
   - Verify story generation works!

---

## 🔧 Configuration Details

### vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    },
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "functions": {
    "api/index.py": {
      "maxDuration": 30
    }
  }
}
```

This configuration:
- Builds Next.js app from `frontend/`
- Sets up Python serverless function from `api/index.py`
- Routes `/api/*` to the FastAPI backend
- Routes everything else to the Next.js frontend
- Sets 30-second timeout for API functions (needed for model loading)

### API Routes

- **Backend:** `https://your-project.vercel.app/api/generate`
- **Health Check:** `https://your-project.vercel.app/api/health`
- **Frontend:** `https://your-project.vercel.app/`

---

## 🐛 Troubleshooting

### Issue: Build fails with "Module not found"

**Solution:**
- Ensure all Python files (`trigram_lm.py`, `train_bpe_tokenizer.py`) are in the root directory
- Check that `requirements.txt` includes `mangum==0.17.0`

### Issue: API returns 503 or "Model not loaded"

**Solution:**
- Check that model files (`trigram_lm.pkl`, `bpe_vocab.json`, `bpe_merges.txt`) are committed to GitHub
- Vercel has a 50MB limit per file - if your model is larger, consider using Vercel Blob Storage
- Check function logs in Vercel dashboard

### Issue: CORS errors

**Solution:**
- Already handled in `api/index.py` with CORS middleware
- If issues persist, check that CORS middleware is properly configured

### Issue: Function timeout

**Solution:**
- Model loading might take time on cold start
- The `maxDuration: 30` in `vercel.json` should help
- Consider using Vercel Pro plan for longer timeouts if needed

### Issue: Frontend can't reach API

**Solution:**
- Ensure frontend uses `/api` path (already configured)
- Check browser console for errors
- Verify API routes are working: `https://your-project.vercel.app/api/health`

---

## 📝 Quick Checklist

Before deploying:
- [ ] Code pushed to GitHub
- [ ] `vercel.json` exists in root
- [ ] `api/index.py` exists
- [ ] `frontend/package.json` exists
- [ ] `requirements.txt` includes `mangum`
- [ ] Model files are committed (or under size limits)
- [ ] All Python dependencies in `requirements.txt`

After deploying:
- [ ] Build succeeds in Vercel dashboard
- [ ] `/api/health` returns 200
- [ ] Frontend loads at root URL
- [ ] Story generation works end-to-end

---

## 🔄 Updating Deployment

**To update your deployment:**

```bash
git add .
git commit -m "Update code"
git push origin main
```

Vercel will automatically:
- Detect the push
- Start a new deployment
- Build and deploy changes
- Keep previous deployment as backup

---

## 💡 Tips

1. **Model File Size:**
   - Vercel free tier has 50MB file size limit
   - If your model is larger, consider:
     - Using Vercel Blob Storage
     - Compressing the model
     - Using a CDN for model files

2. **Cold Starts:**
   - First request after inactivity may be slow (model loading)
   - Subsequent requests are fast (model cached)
   - Consider keeping functions warm with a cron job

3. **Monitoring:**
   - Check Vercel dashboard for function logs
   - Monitor API response times
   - Set up error alerts

4. **Custom Domain:**
   - Add custom domain in Vercel project settings
   - Update DNS records as instructed
   - SSL is automatic

---

## 🎉 Success!

Your Urdu Story Generator is now live on Vercel with both frontend and backend!

**Frontend:** `https://your-project.vercel.app`
**API:** `https://your-project.vercel.app/api/generate`

---

## 📞 Support

If you encounter issues:
1. Check Vercel deployment logs
2. Test API endpoints directly (`/api/health`)
3. Check browser console for frontend errors
4. Verify all files are committed to GitHub
