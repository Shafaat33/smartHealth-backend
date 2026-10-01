from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.activities.booking import release_slot_if_pending


@dataclass
class BookingInput:
    appointment_id: str
    hold_seconds: int


@workflow.defn
class BookingWorkflow:
    @workflow.run
    async def run(self, payload: BookingInput) -> str:
        await workflow.sleep(timedelta(seconds=payload.hold_seconds))
        return await workflow.execute_activity(
            release_slot_if_pending,
            payload.appointment_id,
            start_to_close_timeout=timedelta(seconds=30),
        )
