"""FastAPI-style web adapter (parse-only fixture)."""
import subprocess
import time

from services import core

router = "fastapi_router_placeholder"


@router.get("/items")
async def read_items():
    # Blocking call inside an async def -> stalls the event loop -> a real FINDING.
    time.sleep(0.1)
    return core.used_service()


@router.post("/sync")
def sync_handler():
    # Same class of call in a SYNC def (FastAPI runs it in a threadpool) -> INFORMATIONAL.
    subprocess.run(["echo", "hi"], check=False)
    return "ok"
