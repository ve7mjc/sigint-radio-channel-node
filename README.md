# SigInt Capture Node

Manage the collection, processing, storage, and distribution of realtime two-way radio communication channels.

## Concept of Operation



## Features

* Generate RTLSDR-Airband configuration and wrap/execute process based on config direc
* Apply filter chains (notch, low-pass, high-pass, etc) to audio streams
* Write timestamped voice traffic to disk (wave)
* Reflect voice channels to Mumble in realtime

## RTLSDR-Airband Channel Listeners

RTLSDR-Airband supports output via UDP packets. The output format is an 8,000 byte datagram with 32-bit float samples (2,000 samples) at 16,000 samples/sec. Each datagram contains 125 msec of audio. The datagrams appear to always be 8,000 bytes, with an amount of 0x00 byte padding.



RTLSDR-Airband is falling short in a few ways:

* Saves only MP3 format
* In case of channel with PL 103.5 Hz, a strong first harmonic appears @ 207.0 Hz - Cannot seem to apply multiple notch filters

# Where can RTLSDR-Airband fit in?

We could use it for "efficient" FFT channelizer and CTCSS detection? Could then process the channel signals:

* "RAW" Complex stream could be demodulated, de-emphasized, filtered, etc.
* The UDP audio signal could be passed further along





---


What can our framework do?

* Filter out transmits with no voice content -- eg. many systems will come up and down with a "kerchunk"

## Future Features

### Transmit-Event Metadata

Would be amazing if we could do a better job capturing each "transmit event" -- eg:

* Start Time
* RSSI

