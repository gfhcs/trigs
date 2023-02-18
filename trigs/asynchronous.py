import asyncio


async def first(awaitables):
    """
    Asynchronously waits for the first of the given awaitables to complete, then cancels the others.
    :param awaitables: An iterable of awaitables.
    :return: The result of the first awaitable to complete.
    """
    pending = [asyncio.create_task(a) for a in awaitables]
    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for p in pending:
            p.cancel()
        for d in done:
            if not d.cancelled():
                return d.result()

    raise asyncio.exceptions.CancelledError()
