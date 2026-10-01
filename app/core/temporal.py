from uuid import UUID

from temporalio.client import Client

from app.core.config import BOOKING_HOLD_SECONDS, TEMPORAL_ADDRESS, TEMPORAL_TASK_QUEUE
from app.workflows.booking import BookingInput, BookingWorkflow

_client: Client | None = None


def booking_workflow_id(appointment_id: UUID) -> str:
    return f"booking-{appointment_id}"


async def get_temporal_client() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect(TEMPORAL_ADDRESS)
    return _client


async def start_booking_hold(appointment_id: UUID) -> None:
    client = await get_temporal_client()
    await client.start_workflow(
        BookingWorkflow.run,
        BookingInput(
            appointment_id=str(appointment_id),
            hold_seconds=BOOKING_HOLD_SECONDS,
        ),
        id=booking_workflow_id(appointment_id),
        task_queue=TEMPORAL_TASK_QUEUE,
    )
