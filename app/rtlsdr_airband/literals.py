DEFAULT_SAMPLE_RATE: int = 16000

# 16,000 float32 samples/second (16,000 x 4 per second)
# 8,000 bytes per datagram
# 2,000 samples per datagram
# 125 milliseconds per frame
DEFAULT_STREAM_TIMEOUT_SECS: float = 0.250  # double

RTLSDR_MAX_BANDWIDTH = int(2.56e6)
