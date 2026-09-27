import asyncio
import json
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/logs/{job_id}")
async def websocket_job_logs(websocket: WebSocket, job_id: str):
    await websocket.accept()
    log_templates = [
        "[{time}] [INFO] [Worker-{node}] Dispatching HTTP GET to target URL...",
        "[{time}] [DEBUG] [Worker-{node}] SSL handshake established in {latency}ms (Status: 200 OK)",
        "[{time}] [INFO] [Worker-{node}] Parsing DOM selectors & Schema.org entities...",
        "[{time}] [SUCCESS] [Worker-{node}] Extracted structured JSON payload (Size: {size} KB)",
        "[{time}] [INFO] [Worker-{node}] Discovered internal links, queuing to Redis scraping_pool..."
    ]
    try:
        while True:
            await asyncio.sleep(random.uniform(1.2, 2.5))
            node_id = random.choice(["us-east-1", "eu-west-1", "ap-south-1"])
            template = random.choice(log_templates)
            now_str = asyncio.get_event_loop().time()
            log_msg = template.format(
                time=f"{now_str:.2f}",
                node=node_id,
                latency=random.randint(45, 230),
                size=round(random.uniform(2.4, 18.5), 1)
            )
            await websocket.send_json({
                "job_id": job_id,
                "log": log_msg,
                "node": node_id
            })
    except WebSocketDisconnect:
        pass
