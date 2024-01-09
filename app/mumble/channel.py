from ..dsp.resampling import StreamResampler
from ..radio.schema import SessionFrame
from .certificate import get_certificate, Certificate

import asyncio
import time
import logging
from typing import Optional, Union


# third-party libs
import numpy as np
from pymumble_py3 import Mumble
from pymumble_py3.constants import (
    PYMUMBLE_CLBK_SOUNDRECEIVED as SOUND_RECEIVED,
    PYMUMBLE_CLBK_USERCREATED as USER_CREATED,
    PYMUMBLE_CLBK_USERREMOVED as USER_REMOVED,
    PYMUMBLE_CLBK_CONNECTED as CONNECTED,
    PYMUMBLE_CLBK_DISCONNECTED as DISCONNECTED
)

logger = logging.getLogger(__name__)


DEFAULT_SAMPLE_RATE: int = 48000


class MumbleChannel:

    mumble: Union[Mumble, None]
    resampler: Union[StreamResampler, None]
    sample_rate: int

    last_channel_session_id: Union[int, None]

    # Certificate
    certs_store: str
    cert_cn: str
    certfile: Union[str, None]
    keyfile: Union[str, None]

    def __init__(self, server, port, username, password: str = '',
                 certs_store: Optional[str] = None, **kwargs):

        self.server = server
        self.port = port
        self.username = username
        self.password = password

        self.channel = kwargs.get('channel', None)

        # certificate
        self.certs_store = certs_store
        self.cert_cn = kwargs.get('cert_cn', None)
        self.keyfile = kwargs.get('keyfile', None)
        self.certfile = kwargs.get('certfile', None)

        # defaults/inits
        self.mumble = None
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self.resampler = None  # not initialized until required
        self.audio_buffer = asyncio.Queue()
        self.running = False
        self.stop_requested = False
        self.transmitting = False

        self.last_channel_session_id = None

    async def start(self):

        if self.certs_store is None and self.cert_cn is None:
            logger.warning("cert_store or cert_cn not specified;"
                           "cannot use certs")
        else:
            cert: Certificate = await get_certificate(self.certs_store, self.cert_cn)
            self.keyfile = cert.keyfile
            self.certfile = cert.certfile

        self.mumble = Mumble(self.server, self.username,
                             password=self.password, port=self.port,
                             keyfile=self.keyfile, certfile=self.certfile,
                             reconnect=True)

        self.mumble.callbacks.set_callback(CONNECTED, self.on_connected)
        self.mumble.callbacks.set_callback(DISCONNECTED, self.on_disconnected)

        self.mumble.set_application_string("RadioChannel")

        logger.debug(f"Mumble channel connecting -> \"{self.username}\"@{self.server}:{self.port} ...")

        self.mumble.start()

        # Run is_ready in an executor to prevent blocking
        await asyncio.get_event_loop().run_in_executor(None, self.mumble.is_ready)

        # warning - could be blocking here
        if self.channel:
            self.mumble.channels.find_by_name(self.channel).move_in()

        self.running = True

        await self.stream_audio()

    def stop(self):
        asyncio.run_coroutine_threadsafe(self.audio_buffer.put(None), asyncio.get_event_loop())


    async def stream_audio(self):
        while not self.stop_requested:
            data = await self.audio_buffer.get()
            if data:
                self.transmitting = True
                self.mumble.sound_output.add_sound(data)
            else:
                self.transmitting = False
                await asyncio.sleep(0.01)

    def init_resampler(self, sample_rate_in: int):
        if not self.resampler or self.resampler.rate_in != sample_rate_in:
            self.resampler = StreamResampler(sample_rate_in, self.sample_rate)

    def add_frame(self, frame: SessionFrame):

        # resample if necessary
        if frame.sample_rate != self.sample_rate:
            self.init_resampler(frame.sample_rate)
            frame.samples = self.resampler.process(frame.samples)

        if frame.session_id != self.last_channel_session_id:
            self.resampler.reset()
            self.last_channel_session_id = frame.session_id
            logger.debug(f"new channel session_id '{frame.session_id}' - resetting!")

        # ensure output is pcm s16le
        pcm_data = np.int16(frame.samples * 32767.)
        self.add_samples(pcm_data.tobytes())

    def add_samples(self, pcm_samples: bytearray):
        asyncio.run_coroutine_threadsafe(
            self.audio_buffer.put(pcm_samples),
            asyncio.get_event_loop()
        )

    # Callbacks
    def on_connected(self):
        logger.info(f"Mumble connected: '{self.username}'@{self.server}:{self.port}")

    def on_disconnected(self):
        logger.info(f"Mumble disconnected: '{self.username}'@{self.server}:{self.port}")

    # def sound_received(self, user, soundchunk):
    #     pass  # Handle received sound

    # def user_created(self, user):
    #     pass  # Handle user creation

    # def user_removed(self, user: str, message: str):
    #     # logger.debug(f"mumble: USER_REMOVED {user},{message}")
    #     pass  # Handle user removal

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
