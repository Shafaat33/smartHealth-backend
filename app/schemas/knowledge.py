from pydantic import BaseModel


class IngestionQueued(BaseModel):
    task_id: str
