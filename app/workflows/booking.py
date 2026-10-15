from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.activities.booking import apply_appointment_status, release_slot_if_pending


@dataclass
class BookingInput:
    appointment_id: str
    hold_seconds: int


@workflow.defn
class BookingWorkflow:
    def __init__(self) -> None:
        self._confirmed = False
        self._terminal: str | None = None

    @workflow.signal
    def resolve(self, action: str) -> None:
        if action == "confirm":
            self._confirmed = True
        elif action in ("complete", "canceled"):
            self._terminal = action

    @workflow.run
    async def run(self, payload: BookingInput) -> str:
        try:
            await workflow.wait_condition(
                lambda: self._confirmed or self._terminal is not None,
                timeout=timedelta(seconds=payload.hold_seconds),
            )
        except TimeoutError:
            await workflow.execute_activity(
                release_slot_if_pending,
                payload.appointment_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            return "released"

        if self._terminal is None:
            await workflow.wait_condition(lambda: self._terminal is not None)

        await workflow.execute_activity(
            apply_appointment_status,
            args=[payload.appointment_id, self._terminal],
            start_to_close_timeout=timedelta(seconds=30),
        )
        return self._terminal
