import os

import redis
from fastapi import FastAPI

app = FastAPI()
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
QUEUE_KEY = "jobs"


@app.get("/hello")
def hello():
    return {"message": "Hello from FastAPI"}


@app.post("/jobs")
def enqueue_job():
    redis_client.lpush(QUEUE_KEY, "Hello Worker")
    return {"status": "queued"}
