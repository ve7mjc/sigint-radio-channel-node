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
    r"^Allocating [0-9]+ zero-copy buffers$",
    r"^\[INFO\] Using format C[U|S][0-9]+\.$"
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

    async def run(self):

        bin_path = os.path.join(bin_paths[0], "rtl_airband")
        command = [bin_path, '-F', '-e', '-c', self.config_file]

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


        self.done_event.set()

    # rtl_airband writes ALL output to stderr.. yay!
    async def process_output_task(self):
        while not self.stop_requested.is_set():
            try:
                _, line = await asyncio.wait_for(
                        self.process.output.get(), timeout=0.01)
                logger.debug(f"rtl_airband: {line}")

            except asyncio.TimeoutError:
                pass