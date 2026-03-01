# api/stream.py

import json
import asyncio
import threading
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter

router = APIRouter()

_events: dict[str, list]           = {}
_locks:  dict[str, threading.Lock] = {}
_lock_registry = threading.Lock()


def _get_store(job_id: str):
    with _lock_registry:
        if job_id not in _events:
            _events[job_id] = []
            _locks[job_id]  = threading.Lock()
    return _events[job_id], _locks[job_id]


def _safe_serialize(data: dict) -> dict:
    """
    Recursively convert non-JSON-serializable types to safe equivalents.
    Handles numpy scalars, pandas objects, sets, etc.
    """
    import numpy as np

    def convert(obj):
        # Numpy scalar types
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        # Pandas
        try:
            import pandas as pd
            if isinstance(obj, pd.Series):
                return obj.tolist()
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient="records")
            if isinstance(obj, pd.Timestamp):
                return str(obj)
        except ImportError:
            pass
        # Python builtins
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [convert(i) for i in obj]
        # Fallback — convert to string
        try:
            json.dumps(obj)   # test if already serializable
            return obj
        except (TypeError, ValueError):
            return str(obj)

    return convert(data)


def push_event_sync(job_id: str, event_type: str, data: dict):
    """Called from background thread — stores event in thread-safe list."""
    try:
        # Sanitize before storing — catches problems at the source
        safe_data = _safe_serialize(data)
    except Exception as e:
        print(f"[STREAM] Serialization error for job {job_id} event '{event_type}': {e}")
        safe_data = {"error": "serialization_failed", "event": event_type}

    store, lock = _get_store(job_id)
    with lock:
        store.append({"type": event_type, "data": safe_data})


def cleanup_job(job_id: str):
    with _lock_registry:
        _events.pop(job_id, None)
        _locks.pop(job_id, None)


@router.get("/stream/{job_id}")
async def stream_events(job_id: str):
    """SSE endpoint — browser connects here to receive live updates."""
    _get_store(job_id)

    async def event_generator():
        cursor       = 0
        ping_counter = 0
        max_wait     = 300
        waited       = 0.0

        await asyncio.sleep(0.5)

        while waited < max_wait:
            store, lock = _get_store(job_id)

            with lock:
                new_events = store[cursor:]

            if new_events:
                for event in new_events:
                    cursor += 1
                    try:
                        serialized = json.dumps(event["data"], default=str)
                    except Exception as e:
                        print(f"[STREAM] Failed to serialize event '{event['type']}': {e}")
                        serialized = json.dumps({"error": "serialization_failed"})

                    yield {
                        "event": event["type"],
                        "data":  serialized
                    }

                    if event["type"] in ("done", "error"):
                        return
            else:
                ping_counter += 1
                waited       += 0.2
                if ping_counter % 15 == 0:
                    yield {
                        "event": "ping",
                        "data":  json.dumps({"t": ping_counter})
                    }

            await asyncio.sleep(0.2)

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        }
    )