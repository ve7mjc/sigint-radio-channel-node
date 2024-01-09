sensor -> signal acquisition -> pipeline
  |          ^--- metadata: timestamp, frequency
  `-- metadata: geospatial, type, frequency?


fully abstracted, we would be looking at a raw stream captured from a sensor
then hits an acquisition adapter with a header, routing it through its lifetime

an "RTLSDR-Airband FFT Channelizing" pipeline is still a sensor tuned to a frequency in a sense

detection/acquisition event -- aka "channel activity event"


- It is realistic that two receivers tuned to the same frequency but at different locations can produce entirely different outcomes
  thus, the "sensor location" is as important as the "rf frequency" when it comes to identifying a radiochannel event
- We want to capture the "receiver settings" that produced the received signal waveform -- differences here may drastically change the outcome
  - receiver type: eg. 8-bit RTLSDR
  - Receiver gain, sample rate
- We could run a "sidecar" model temporarily, or in parallel so that we can run without a server? Each event gets placed in a json file next to the recording with all the information for processing.
- SigMF is a solid idea for a metadata sidecar - but it would be even more appropriate if we were writing the raw IQ samples to disk


```python
@dataclass
class SensorEvent:
    sensor_id: str
    timestamp: str

```




```python
@dataclass
class Sensor:
    id: str


```
