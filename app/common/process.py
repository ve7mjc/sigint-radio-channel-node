from asyncio import StreamReader, Queue, Event, QueueEmpty
from asyncio.subprocess import PIPE, Process
import asyncio
from typing import Union, Optional, Any
from time import time
import logging
import re
from enum import Enum
import traceback
from dataclasses import dataclass, field


class ProcessEventType(Enum):
    READY = 0
    READY_TIMEOUT = 1
    EXCEPTION = 3
    EXIT = 4

@dataclass
class ProcessEvent:
    type: ProcessEventType
    message: Optional[str] = None
    args: dict[str, Any] = field(default_factory=dict)


logger = logging.getLogger(__name__)

class ReadyTimeout(Exception):
    pass


# Wrap an asyncio.Process
class ProcessTask:

    _process: Union[Process, None]
    _tasks: list[asyncio.Task]

    _ready_patterns: list[str]
    _ready_timeout_secs: Optional[float]

    start_time: Union[float, None]
    events: Queue[ProcessEvent]
    output: Queue[str]
    stop_requested: Event

    ready_event: Event

    def __init__(self, output_queue: Queue[str] = None,
                 ready_patterns: list[str] = [],
                 ready_timeout: Optional[float] = None):

        self.output = output_queue or Queue()
        self._ready_patterns = ready_patterns
        self._ready_timeout_secs = ready_timeout

        self._process = None
        self._tasks = []
        self.start_time = None
        self.events = Queue()
        self.stop_requested = Event()
        self.ready_event = Event()

    async def run(self, command: list[str]):

        logger.debug(f"ProcessTask command: {' '.join(command)}")

        self._process = await asyncio.create_subprocess_exec(
                *command, stdout=PIPE, stderr=PIPE)

        self._tasks.extend([
            asyncio.create_task(self._read_stream(self._process.stdout)),
            asyncio.create_task(self._read_stream(self._process.stderr, stderr=True))
        ])

        self.start_time = time()

        try:
            await asyncio.wait_for(self.ready_event.wait(),
                                timeout=self._ready_timeout_secs)
            logger.debug("process ready!")
        except asyncio.TimeoutError:
            await self.events.put(
                ProcessEvent(
                    type=ProcessEventType.READY_TIMEOUT
                ))

        try:
            await asyncio.gather(*self._tasks)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"exceptions from gather() = {e}")
            print("Traceback:", tb)

        return_code = await self._process.wait()

        await self.events.put(
            ProcessEvent(
                type=ProcessEventType.EXIT,
                args={'return_code': return_code}
            )
        )

    async def stop(self):
        self.stop_requested.set()
        self._process.kill()


    async def _read_stream(self, stream: StreamReader, stderr: bool = False):
            pipe: str = "stderr" if stderr else "stdout"
            while not self.stop_requested.is_set():
                line = await stream.readline()
                if line:
                    line = line.decode().strip()

                    # Check for ready condition
                    if not self.ready_event.is_set():
                        for pattern in self._ready_patterns:
                            if re.match(pattern, line):
                                await self._set_ready(message=line)

                    await self.output.put((pipe, line))

                else:
                    break

    async def _set_ready(self, message: Optional[str] = None):
        await self.events.put(ProcessEvent(
            type=ProcessEventType.READY,
            message=message))
        self.ready_event.set()

    @property
    def is_ready(self):
        return self.ready_event.is_set()

    @property
    def runtime_secs(self) -> Union[float, None]:
        if self.start_time is None:
            return None
        return time() - self.start_time
