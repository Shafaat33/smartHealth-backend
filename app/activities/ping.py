from temporalio import activity


@activity.defn
async def ping() -> str:
    return "ok"
