from app.common.process import ProcessTask, ProcessEvent, ProcessEventType

import os
import asyncio
from asyncio import Queue, Event
from typing import Optional

import logging

logger = logging.getLogger(__name__)

bin_paths: list[str] = [
    "/usr/local/bin"
]

default_timeout_ready_secs: float = 5.

PROCESS_READY_PATTERNS: list[str] = [
    r"^Allocating [0-9]+ zero-copy buffers$"
]

class RtlSdrAirbandInstance:

    id: str

    config_file: str

    events: Queue[ProcessEvent]
    stop_requested: Event

    ready_timeout_secs: float

    _tasks: list

    process: ProcessTask

    def __init__(self, config_file: str, id: Optional[str] = None):

        self.config_file = config_file
        self.id = id

        self.ready_timeout_secs = default_timeout_ready_secs
        self.ready = False

        self.stop_requested = Event()
        self.done_event = Event()

        self._tasks = []
        self.events = Queue()

        self.process = ProcessTask(ready_patterns=PROCESS_READY_PATTERNS,
                                   ready_timeout=5)

    # async def wait_for_ready(self):
    #     await self.ready_event.wait()

    # async def wait_for_process(self):
    #     await self.process.wait()

    async def run(self):

        bin_path = os.path.join(bin_paths[0], "rtl_airband")
        command = [bin_path, '-F', '-c', self.config_file]

        self._tasks.append(asyncio.create_task(self.process_output_task()))

        process_task = asyncio.create_task(
                self.process.run(command), name="process_task")

        try:
            timeout_ready_secs = default_timeout_ready_secs

            while not self.stop_requested.is_set():
                event = await self.process.events.get()
                await self.events.put(event)

        except Exception as e:
            logger.error(f"error type == {type(e)} {e}")
            # await asyncio.wait_for(self.ready_event.wait(),
            #                        timeout=timeout_ready_secs)
        except asyncio.TimeoutError:
            logger.error("rtl_airband timed out")


        # return_code = await self.process.wait()

        self.done_event.set()

    async def process_output_task(self):
        while not self.stop_requested.is_set():
            try:
                pipe, line = await asyncio.wait_for(
                        self.process.output.get(), timeout=0.01)
                if pipe == "stderr":
                    logger.error(f"ERROR output [{pipe}]: {line}")
                else:
                    logger.debug(f"ERROR output [{pipe}]: {line}")
            except asyncio.TimeoutError:
                pass