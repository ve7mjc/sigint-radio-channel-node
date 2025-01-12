
## Development Pathways

How can we modularize this functionality?

- RTLSDR -> RTLSDR-Airband(rtl_airband) -> Async UDP PCM -> WAV RECORDING
                                                         -> Mumble Encoding -> Mumble Server
                                                         -> Detections/Analysis

### Pains

- Adding/Changing channels is difficult (2025-01-04) as the entire process must shut down, which results in Mumble channels parting/joining the channels, etc.



## Concepts

sensor -> signal acquisition -> pipeline
  |          ^--- metadata: timestamp, frequency
  `-- metadata: geospatial, type, frequency?

### STREAMS and OBJECTS

STREAM
-- for some problems we require near-realtime block-of-samples moving through a pipeline (ie. acquisition, filtering, encoding)
- we may be producing realtime metadata such as time-series power measurements or FFTs (tone-detection, etc) against a stream
- Ideally, a stream would be communicated via a metadata event/header -- we know many things but we do not know number of samples (duration, size, time of ceasation)


CAPTURE
-- for others, we are better suited to process the "intercept" after it has occurred (ie.. ptt intercepts)
MinIO/S3 "capture" objects apply here
Perhaps - in some ways, we could process these captures much like they are in fact streams -- many things operations (such as resampling) are far less computational effort and higher quality when number of samples is known.


-- Working somewhat "backwards" -- perhaps we write our Intercept API now - and meld the collector into it?


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
