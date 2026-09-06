from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    EvaluatePatchRequest,
    PatchResponse,
)
from .nemotron import NemotronError, analyze_context, evaluate_patch


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="The Missing Question",
    description="Adversarial reasoning sidecar for AI-assisted builders",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze_context", response_model=AnalyzeResponse)
async def analyze_context_endpoint(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze_context(req.context.strip(), req.mode)
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
