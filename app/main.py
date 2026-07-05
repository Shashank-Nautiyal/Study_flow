import os
import tempfile
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.orchestrator import Orchestrator
from app.services.pdf_service import PDFService
from app.services.web_service import WebService
from app.services.youtube_service import YouTubeService


app = FastAPI(title="Study Flow")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


class RouteActionRequest(BaseModel):
    user_id: str = "demo-user"
    action_type: str
    payload: Dict[str, Any] = {}


class UrlExtractRequest(BaseModel):
    url: str
    source_type: Optional[str] = None


def infer_source_type(url: str, explicit_type: Optional[str] = None) -> str:
    if explicit_type and explicit_type != "auto":
        return explicit_type

    lowered = url.lower()
    if "youtube.com" in lowered or "youtu.be" in lowered:
        return "youtube"
    return "web"


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/route-action")
def route_action(request: RouteActionRequest):
    try:
        result = orchestrator.route_action(
            request.user_id,
            request.action_type,
            request.payload,
        )
        return {"ok": True, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/extract/url")
def extract_url(request: UrlExtractRequest):
    source_type = infer_source_type(request.url, request.source_type)

    if source_type == "youtube":
        content = YouTubeService.get_transcript(request.url)
    elif source_type == "web":
        content = WebService.scrape_url(request.url)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source_type: {source_type}")

    return {
        "source_type": source_type,
        "content": content,
        "character_count": len(content or ""),
    }


@app.post("/api/extract/pdf")
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    temp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await file.read())

        content = PDFService.extract_text(temp_path)
        return {
            "source_type": "pdf",
            "content": content,
            "character_count": len(content or ""),
            "filename": file.filename,
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
