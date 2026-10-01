from temporalio.client import Client

from app.core.config import TEMPORAL_ADDRESS

_client: Client | None = None


async def get_temporal_client() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect(TEMPORAL_ADDRESS)
    return _client
