from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import yt_dlp

app = FastAPI(title="apeXion Downloader Worker")


class InfoRequest(BaseModel):
    url: HttpUrl
    quality: Optional[str] = None


class DownloadRequest(BaseModel):
    url: HttpUrl
    quality: Optional[str] = None


def _ydl_opts(quality: Optional[str]) -> dict:
    # Adjust formats to your needs; ffmpeg must be available on the worker host.
    fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"
    if quality:
        # Non-strict quality hint; falls back to best if unavailable.
        fmt = f"bv*[height<={quality.replace('p','')}]+ba/b[height<={quality.replace('p','')}]/{fmt}"
    return {
        "format": fmt,
        "noplaylist": True,
        "quiet": True,
    }


@app.post("/info")
async def info(payload: InfoRequest):
    opts = _ydl_opts(payload.quality)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            data = ydl.extract_info(str(payload.url), download=False)
    except Exception as exc:  # broad to surface upstream errors
        raise HTTPException(status_code=400, detail=f"Failed to fetch info: {exc}")

    return {
        "title": data.get("title"),
        "duration": data.get("duration"),
        "thumbnail": data.get("thumbnail"),
        "uploader": data.get("uploader"),
        "message": "Metadata fetched",
    }


@app.post("/download")
async def download(payload: DownloadRequest):
    opts = _ydl_opts(payload.quality)
    tmp_dir = Path(tempfile.gettempdir()) / "apexion_dl"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Save to temp; in production, upload to object storage and return a signed URL.
    opts.update({
        "outtmpl": str(tmp_dir / "%(title)s.%(ext)s"),
    })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([str(payload.url)])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Download failed: {exc}")

    # Pick the newest file in the temp dir as the result.
    candidates = sorted(tmp_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise HTTPException(status_code=500, detail="No file produced")

    file_path = candidates[0]
    return {
        "file": file_path.name,
        "path": str(file_path),
        "message": "Download finished. Upload this file to storage and return a signed URL in production.",
    }


@app.get("/")
async def root():
    return {"ok": True, "message": "apeXion worker online"}
