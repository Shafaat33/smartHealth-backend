import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.activities.booking import release_slot_if_pending
from app.activities.ping import ping
from app.core.config import TEMPORAL_ADDRESS, TEMPORAL_TASK_QUEUE
from app.workflows.booking import BookingWorkflow
from app.workflows.ping import PingWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _connect() -> Client:
    while True:
        try:
            client = await Client.connect(TEMPORAL_ADDRESS)
            logger.info("Connected to Temporal at %s", TEMPORAL_ADDRESS)
            return client
        except Exception:
            logger.warning("Temporal not ready at %s, retrying...", TEMPORAL_ADDRESS)
            await asyncio.sleep(2)


async def main() -> None:
    client = await _connect()
    worker = Worker(
        client,
        task_queue=TEMPORAL_TASK_QUEUE,
        workflows=[PingWorkflow, BookingWorkflow],
        activities=[ping, release_slot_if_pending],
    )
    logger.info("Worker listening on %s", TEMPORAL_TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
