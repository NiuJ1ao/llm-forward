import asyncio
from backend.usage import UsageRecord


class UsageSink:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.writers = []

    def add_writer(self, writer):
        self.writers.append(writer)

    async def record(self, usage: UsageRecord):
        await self.queue.put(usage)

    async def worker(self):
        while True:
            usage = await self.queue.get()

            for writer in self.writers:
                try:
                    await writer.write(usage)
                except Exception as e:
                    # Never break the pipeline
                    print("[usage-writer-error]", e)

            self.queue.task_done()
