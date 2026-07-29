import os
import shutil
from pathlib import Path

import psutil
import redis
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

import rag
from rag import DOCUMENTS_PATH, chat, process_documents

app = FastAPI()
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
QUEUE_KEY = "jobs"

Path(DOCUMENTS_PATH).mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    try:
        redis_client.ping()
        redis_status = "connected"
    except redis.ConnectionError:
        redis_status = "disconnected"

    return {
        "status": "healthy" if redis_status == "connected" else "unhealthy",
        "redis": redis_status,
        "disk_used_percent": int(psutil.disk_usage("/").percent),
        "memory_used_percent": int(psutil.virtual_memory().percent),
    }


@app.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    for file in files:
        dest = Path(DOCUMENTS_PATH) / file.filename
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    process_documents()
    return {"status": "indexed"}


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    if not rag.document_uploaded:
        raise HTTPException(status_code=400, detail="Upload documents first")
    answer = chat(req.message)
    return {"answer": answer}


@app.post("/jobs")
def enqueue_job():
    redis_client.lpush(QUEUE_KEY, "Hello Worker")
    return {"status": "queued"}
