# api/stream.py  ← FULL FILE, replace everything

import json
import asyncio
import threading
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter

router = APIRouter()

# Thread-safe event storage per job
_events: dict[str, list] = {}
_locks: dict[str, threading.Lock] = {}


def _get_store(job_id: str):
    if job_id not in _events:
        _events[job_id] = []
        _locks[job_id] = threading.Lock()
    return _events[job_id], _locks[job_id]


def push_event_sync(job_id: str, event_type: str, data: dict):
    """Called from background thread — stores event in thread-safe list."""
    store, lock = _get_store(job_id)
    with lock:
        store.append({"type": event_type, "data": data})


@router.get("/stream/{job_id}")
async def stream_events(job_id: str):
    """SSE endpoint — browser connects here to receive live updates."""

    # Ensure store exists
    _get_store(job_id)

    async def event_generator():
        cursor = 0  # Track how many events we've already sent

        while True:
            store, lock = _get_store(job_id)

            with lock:
                new_events = store[cursor:]

            for event in new_events:
                cursor += 1
                yield {
                    "event": event["type"],
                    "data": json.dumps(event["data"])
                }
                if event["type"] == "done" or event["type"] == "error":
                    return

            # No new events yet — wait and poll again
            await asyncio.sleep(0.2)

    return EventSourceResponse(event_generator())