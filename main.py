import os
import logging
from fastapi import FastAPI, HTTPException, Body, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import tempfile

from app.agents.orchestrator import Orchestrator
from app.services.youtube_service import YouTubeService
from app.services.pdf_service import PDFService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Study Flow API")

# Setup CORS for local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator globally
orchestrator = Orchestrator()

# --- Models ---
class ExtractUrlRequest(BaseModel):
    url: str
    source_type: Optional[str] = "auto"

class RouteActionRequest(BaseModel):
    user_id: str
    action_type: str
    payload: Dict[str, Any] = {}

# --- Endpoints ---
@app.post("/api/extract/url")
def extract_url(req: ExtractUrlRequest):
    """
    Extracts content or metadata from a URL.
    Instantly returns playlist metadata if it's a YouTube playlist.
    Otherwise, extracts the single video transcript or webpage text.
    """
    logger.info(f"Extracting URL: {req.url} (Type: {req.source_type})")
    
    is_youtube = "youtube.com" in req.url or "youtu.be" in req.url
    
    if is_youtube or req.source_type == "youtube":
        if YouTubeService.is_playlist(req.url):
            logger.info("Detected YouTube Playlist. Fetching metadata...")
            meta = YouTubeService.get_playlist_metadata(req.url)
            if "error" in meta:
                raise HTTPException(status_code=400, detail=meta["error"])
            # Return playlist metadata directly for Phase 1
            return {"source_type": "youtube_playlist", "content": meta}
        else:
            logger.info("Detected single YouTube video. Fetching transcript...")
            transcript = YouTubeService.get_transcript(req.url)
            if transcript.startswith("Error:"):
                raise HTTPException(status_code=400, detail=transcript)
            return {"source_type": "youtube", "content": transcript}
    else:
        # Web scraping fallback (placeholder until web scraper service is added)
        raise HTTPException(status_code=501, detail="Web scraping not yet implemented.")


@app.post("/api/route-action")
def route_action(req: RouteActionRequest):
    """
    Wraps the Orchestrator to route all agent actions.
    """
    logger.info(f"Routing action: {req.action_type} for user {req.user_id}")
    try:
        result = orchestrator.route_action(req.user_id, req.action_type, req.payload)
        return {"ok": True, "result": result}
    except ValueError as e:
        logger.error(f"Value Error routing action: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error routing action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
