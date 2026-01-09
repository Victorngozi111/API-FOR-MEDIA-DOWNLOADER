# apeXion Downloader Worker (Render)

A minimal FastAPI service that exposes `/info` and `/download`, using `yt-dlp` + `ffmpeg`. Deploy to Render as a Web Service and point your Vercel front-end env `REMOTE_WORKER_URL` at the Render URL.

## Endpoints
- `POST /info` → `{ url, quality? }` → returns `title`, `duration`, `thumbnail`, `uploader`, `message`.
- `POST /download` → `{ url, quality? }` → downloads to a temp file. In production, upload the file to object storage and return a signed URL.
- `GET /` → health check.

## Deploy to Render
1) Create a new **Web Service** from this folder.
2) Runtime: Python. Build command: `pip install -r requirements.txt`. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
3) Ensure `ffmpeg` is available. On Render, add a build step or use a base image that includes ffmpeg (or install via `apt` in a custom Dockerfile if needed).
4) After deploy, set the Vercel env var `REMOTE_WORKER_URL` to the Render service URL (e.g., `https://your-worker.onrender.com`).

## Notes
- The `/download` endpoint currently saves to `/tmp/apexion_dl` and returns the file name/path. Replace the return with a signed URL from S3/Spaces/etc. after uploading the file there.
- Adjust `_ydl_opts` in `app.py` to tune formats/quality.
- If you need CORS, add `fastapi.middleware.cors` middleware.
