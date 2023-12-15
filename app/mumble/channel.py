import asyncio
import time
import logging
from typing import Optional


# third-party libs
import numpy as np
from pymumble_py3 import Mumble
from pymumble_py3.constants import (
    PYMUMBLE_CLBK_SOUNDRECEIVED as SOUND_RECEIVED,
    PYMUMBLE_CLBK_USERCREATED as USER_CREATED,
    PYMUMBLE_CLBK_USERREMOVED as USER_REMOVED
)

logger = logging.getLogger(__name__)


class MumbleChannel:
    def __init__(self, server, port, username, password: str = '', **kwargs):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.channel = kwargs.get('channel', None)
        self.mumble = None
        self.audio_buffer = asyncio.Queue()
        self.running = False
        self.stop_requested = False
        self.transmitting = False

    async def start(self):

        self.mumble = Mumble(self.server, self.username, password=self.password, port=self.port)

        self.mumble.callbacks.set_callback(SOUND_RECEIVED, self.sound_received)
        self.mumble.callbacks.set_callback(USER_CREATED, self.user_created)
        self.mumble.callbacks.set_callback(USER_REMOVED, self.user_removed)

        self.mumble.set_application_string("MumbleChannelBot")

        logger.debug(f"connecting to Mumble server - {self.username}@{self.server}:{self.port} ...")

        self.mumble.start()

        # Run is_ready in an executor to prevent blocking
        await asyncio.get_event_loop().run_in_executor(None, self.mumble.is_ready)

        # warning - could be blocking here
        if self.channel:
            logger.debug(f"joining channel '{self.channel}'")
            self.mumble.channels.find_by_name(self.channel).move_in()

        self.running = True

        logger.info(f"mumble client ready! ('{self.username}'@{self.server}:{self.port})")

        await self.stream_audio()

    def stop(self):
        asyncio.run_coroutine_threadsafe(self.audio_buffer.put(None), asyncio.get_event_loop())
        self.mumble.stop()  # not sure if this is right

    async def stream_audio(self):
        while not self.stop_requested:
            data = await self.audio_buffer.get()
            if data:
                self.transmitting = True
                self.mumble.sound_output.add_sound(data)
            else:
                self.transmitting = False
                await asyncio.sleep(0.1)  # Short pause to prevent busy waiting

    def add_samples(self, samples):
        asyncio.run_coroutine_threadsafe(self.audio_buffer.put(samples), asyncio.get_event_loop())

    # Callbacks
    def sound_received(self, user, soundchunk):
        pass  # Handle received sound

    def user_created(self, user):
        pass  # Handle user creation

    def user_removed(self, user: str, message: str):
        # logger.debug(f"mumble: USER_REMOVED {user},{message}")
        pass  # Handle user removal

# Usage example
async def main():
    mumble_channel = MumbleChannel("your_mumble_server", 64738, "MumbleBot", "your_password", "your_channel")
    await mumble_channel.start()

    # Add samples to the buffer
    sine_wave = np.sin(np.linspace(0, 2 * np.pi, 48000)).astype(np.float32).tobytes()
    mumble_channel.add_samples(sine_wave)

    # Stop after some time
    await asyncio.sleep(5)
    mumble_channel.stop()


if __name__ == "__main__":
    asyncio.run(main())



# # Constants
# SERVER = "172.23.0.40"
# PORT = 64738  # Default Mumble port
# USERNAME = "SineWaveBot"
# # PASSWORD = "your_password"  # if required
# CHANNEL = "your_channel"  # Channel name to join
# SAMPLE_RATE = 48000  # Sample rate of the audio
# SINE_FREQ = 800  # Frequency of the sine wave
# CHUNK_SIZE = 1024  # Size of each audio chunk
# DURATION = 0.1  # Duration of each audio chunk in seconds

# # Generate a sine wave
# def generate_sine_wave(freq, sample_rate, duration):
#     t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
#     return np.sin(2 * np.pi * freq * t)

# # Connect to Mumble server
# mumble = Mumble(SERVER, user=USERNAME, port=PORT)  # password=PASSWORD,
# mumble.start()
# mumble.is_ready()

# # Join a channel
# # mumble.channels.find_by_name(CHANNEL).move_in()

# # Stream the sine wave
# try:
#     while True:
#         sine_wave = generate_sine_wave(SINE_FREQ, SAMPLE_RATE, DURATION)
#         mumble.sound_output.add_sound(sine_wave.tobytes())
#         time.sleep(DURATION)
# except KeyboardInterrupt:
#     # Disconnect from the server
#     mumble.stop()
