# Urdu Story Frontend (Phase V)

This is a small Next.js web UI that connects to your existing **Urdu Trigram Language Model FastAPI backend** and displays story completions in a **chatGPT-style, step-wise animation**.

## Tech Stack

- Next.js 14 (App Router)
- React 18
- Deployed on Vercel

## Running Locally

From the project root:

```bash
cd frontend
npm install
npm run dev
```

By default the UI expects your FastAPI backend on:

- `http://localhost:8000`

You can override this using:

```bash
NEXT_PUBLIC_API_BASE_URL="https://your-backend-url" npm run dev
```

## Environment Variable

- `NEXT_PUBLIC_API_BASE_URL` – base URL of the FastAPI service (e.g. your Vercel / Render / other deployment). Defaults to `http://localhost:8000` for development.

The UI calls:

- `POST ${NEXT_PUBLIC_API_BASE_URL}/generate`

with the same JSON body described in `README_API.md`.

## Deploying on Vercel

1. Create a new Vercel project pointing to the `frontend/` directory as the root.
2. Set the **Environment Variable**:
   - `NEXT_PUBLIC_API_BASE_URL=https://your-fastapi-backend-domain`
3. Deploy.

> The FastAPI backend can be deployed separately (e.g., another Vercel Python project, Docker on a VPS, etc.) as long as it exposes the `/generate` endpoint over HTTPS.

