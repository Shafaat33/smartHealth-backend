from uuid import uuid4

from fastapi import APIRouter

from app.constants import TEMPORAL_URL
from app.core.config import TEMPORAL_TASK_QUEUE
from app.core.temporal import get_temporal_client
from app.workflows.ping import PingWorkflow

router = APIRouter(prefix=TEMPORAL_URL, tags=["temporal"])


@router.post("/ping")
async def temporal_ping():
    client = await get_temporal_client()
    result = await client.execute_workflow(
        PingWorkflow.run,
        id=f"ping-{uuid4()}",
        task_queue=TEMPORAL_TASK_QUEUE,
    )
    return {"result": result}
