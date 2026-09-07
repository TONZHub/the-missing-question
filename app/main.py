from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .mcp_server import mcp, mcp_app
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    EvaluatePatchRequest,
    FollowUpRequest,
    FollowUpResponse,
    PatchResponse,
)
from .nemotron import NemotronError, analyze_context, evaluate_follow_up, evaluate_patch


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="The Missing Question",
    description="Adversarial reasoning sidecar for AI-assisted builders",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/privacy", include_in_schema=False)
async def privacy() -> FileResponse:
    return FileResponse(STATIC_DIR / "privacy.html")


@app.get("/terms", include_in_schema=False)
async def terms() -> FileResponse:
    return FileResponse(STATIC_DIR / "terms.html")


@app.get("/support", include_in_schema=False)
async def support() -> FileResponse:
    return FileResponse(STATIC_DIR / "support.html")


@app.get("/.well-known/openai-apps-challenge", include_in_schema=False)
async def openai_apps_challenge() -> PlainTextResponse:
    token = os.getenv("OPENAI_APPS_CHALLENGE", "").strip()
    if not token:
        raise HTTPException(status_code=404, detail="Challenge token not configured")
    return PlainTextResponse(token, media_type="text/plain")


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze_context", response_model=AnalyzeResponse)
async def analyze_context_endpoint(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze_context(req.context.strip(), req.mode)
    except NemotronError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/follow_up", response_model=FollowUpResponse)
async def follow_up_endpoint(req: FollowUpRequest) -> FollowUpResponse:
    try:
        return evaluate_follow_up(
            original_concern=req.original_concern.model_dump(),
            follow_up=req.follow_up.strip(),
            updated_context=req.updated_context,
        )
    except NemotronError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/evaluate_patch", response_model=PatchResponse)
async def evaluate_patch_endpoint(req: EvaluatePatchRequest) -> PatchResponse:
    try:
        return evaluate_patch(
            original_concern=req.original_concern.model_dump(),
            resolution=req.resolution.strip(),
            updated_context=req.updated_context,
        )
    except NemotronError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


app.mount("/", mcp_app)
