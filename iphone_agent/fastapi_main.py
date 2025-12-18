from fastapi import FastAPI
from fastapi.responses import JSONResponse
import threading
from pydantic import BaseModel

app = FastAPI()

# Global variables for storing content in memory
# Lock to ensure thread safety under concurrent access
content_lock = threading.Lock()


class ContentPayload(BaseModel):
    content: str
    launch_app: bool

CONTENT_CACHE = ContentPayload(content="", launch_app=False)

@app.post("/content")
def set_content(payload: ContentPayload):
    """Set the latest content (in-memory only; not persisted to disk)."""
    global CONTENT_CACHE
    print("Received content:", payload)

    with content_lock:
        CONTENT_CACHE = payload
    if payload.launch_app:
        return JSONResponse({"success": True, "content": CONTENT_CACHE.content, "launch_app": payload.launch_app})

    return JSONResponse({"success": True, "content": CONTENT_CACHE.content})


@app.get("/content")
def get_latest_content():
    """
    Get the latest content (in-memory only).
    """
    global CONTENT_CACHE

    with content_lock:
        payload = CONTENT_CACHE
    if payload.launch_app:
        return JSONResponse({"success": True, "content": CONTENT_CACHE.content, "launch_app": payload.launch_app})

    return JSONResponse({"success": True, "content": CONTENT_CACHE.content})