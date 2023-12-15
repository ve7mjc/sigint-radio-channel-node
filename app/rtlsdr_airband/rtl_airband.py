import os
import asyncio
from asyncio import StreamReader, Queue, Event
from asyncio.subprocess import PIPE
import logging

logger = logging.getLogger(__name__)

bin_paths: list[str] = [
    "/usr/local/bin"
]

default_timeout_ready_secs: float = 5.

class RtlSdrAirbandInstance:

    config_file: str
    output_queue: Queue[str]

    ready: bool

    stop_requested: Event
    ready_event: Event
    done_event: Event


    def __init__(self, config_file: str):
        self.config_file = config_file
        self.output_queue = Queue()

        self.stop_requested = Event()
        self.ready_event = Event()
        self.done_event = Event()

        self.ready = False

    async def _read_stream(self, stream: StreamReader, stderr: bool = False):
        while not self.stop_requested.is_set():
            line = await stream.readline()
            if line:
                line = line.decode().strip()
                if not self.ready and "Allocating 10 zero-copy buffers" in line:
                    self.ready_event.set()
                    logger.debug("rtl_airband running!")
                logger.debug("rtl_airband -> output: %s", line)
                await self.output_queue.put(line)
            else:
                break

    async def _process_output_task(self):
        pass

    async def run(self):

        bin_path = os.path.join(bin_paths[0], "rtl_airband")
        command = [bin_path, '-F', '-c', self.config_file]
        timeout_ready_secs = default_timeout_ready_secs

        logger.debug(f"calling: {' '.join(command)}")

        process = await asyncio.create_subprocess_exec(
                *command, stdout=PIPE, stderr=PIPE)

        try:
            await asyncio.gather(
                self._read_stream(process.stdout, stderr=False),
                self._read_stream(process.stderr, stderr=True),
                self._process_output_task()
            )
            await process.wait()

            # After the specific output is found, continue capturing output
            # await asyncio.wait_for(process.wait(), timeout=timeout_ready_secs)

        except asyncio.TimeoutError:
            logger.error("process timed out!")
        finally:
            process.kill()
            await process.wait()
            self.done_event.set()
            logger.info("process ended")
