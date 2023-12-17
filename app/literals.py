DEFAULT_CONFIG_FILE: str = "config.yaml"
DEFAULT_UDP_LISTEN_ADDR: str = "127.0.0.1"
DEFAULT_UDP_PORT_BASE: int = 6000
DEFAULT_PTT_TIMEOUT_SECS: float = 0.120  # 120 mS

DEFAULT_MINIMUM_VOICE_ACTIVE_SECS: float = 0.3

# The default number of samples per voice frame in Mumble is 480. This is based on a sample rate of 48 kHz and a frame size of 10 ms, which is a common configuration in VoIP applications.
SAMPLE_SECS_PER_FRAME: int = 10 / 1000  # 10 ms

DEFAULT_DATA_STORE_PATH: str = "/opt/data/radio_channels"
