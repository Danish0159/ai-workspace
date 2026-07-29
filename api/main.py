import os
import shutil
import time
from pathlib import Path

import psutil
import redis
from fastapi import FastAPI, File, HTTPException, UploadFile
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

import rag
from rag import DOCUMENTS_PATH, chat, process_documents

app = FastAPI()

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
CPU_USAGE_PERCENT = Gauge("cpu_usage_percent", "CPU usage percentage")
MEMORY_USAGE_PERCENT = Gauge("memory_usage_percent", "Memory usage percentage")
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
QUEUE_KEY = "jobs"

Path(DOCUMENTS_PATH).mkdir(parents=True, exist_ok=True)


@app.middleware("http")
async def track_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    method = request.method
    path = request.url.path
    status = response.status_code

    HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=status).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)

    return response


@app.get("/metrics")
def metrics():
    CPU_USAGE_PERCENT.set(psutil.cpu_percent(interval=0))
    MEMORY_USAGE_PERCENT.set(psutil.virtual_memory().percent)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


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
