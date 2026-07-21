import os
import time

import redis

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/0"),
    socket_timeout=None,
)
QUEUE_KEY = "jobs"

while True:
    _, job = redis_client.brpop(QUEUE_KEY)
    print(job.decode())
    time.sleep(5)
    print("Job completed")
