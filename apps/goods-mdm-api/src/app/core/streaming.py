"""StreamingResponse that closes its synchronous producer on every ASGI exit."""
import anyio
from starlette.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse


class ClosingStreamingResponse(StreamingResponse):
    def __init__(self, iterator, **kwargs):
        self.producer = iterator
        super().__init__(iterator, **kwargs)

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            # Starlette's threadpool iterator does not promise to close the
            # underlying sync generator on disconnect. Shield cleanup from the
            # response's cancellation scope, after any active next() has ended.
            with anyio.CancelScope(shield=True):
                await run_in_threadpool(self.producer.close)
