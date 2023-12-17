# sigint Radio Channel Capture Node

Manage the simulataneous collection, processing, storage, and distribution of real-time two-way radio communication channels.

## Concept of Operation

User defines stream sources (SDR device(s) for now) and the radio channels. The channel manager will produce an RTLSDR-Airband configuration file, subprocess an rtl_airband binary with provided configuration, and then configure requisite number of UDP channels needed to match RTLSDR-Airband.

Each channel "gates" the stream with either CSQ/CTCSS per rtl_airband, applies multiple audio filters, writes the wave data to disk, while simultaneously upsampling the streams and passing them to a Mumble server with each channel being a "user".

## Features

* Automatically generate RTLSDR-Airband configuration
  * Permit global, device, and channel specific overrides in the natural format of rtl_airband
* Subprocess/wrap the rtl_airband process with generated configuration file. Waits for rtl_airband to become "ready" and also monitors for premature exit/exception.
* Apply filter chains (notch, low-pass, high-pass, etc) to audio streams
* Write timestamped voice traffic to disk (wav)
* Redirect voice channels to Mumble in realtime

## RTLSDR-Airband Channel Listeners

RTLSDR-Airband supports output via UDP packets. The output format is an 8,000 byte datagram with 32-bit float samples (2,000 samples) at 16,000 samples/sec. Each datagram contains 125 msec of audio. The datagrams appear to always be 8,000 bytes, with an amount of 0x00 byte padding.

RTLSDR-Airband falls short in a few ways:

* Saves only MP3 format
* Filter options are limited - eg. only one notch per channel and the high/low-pass filters are only available under certain conditions.

# Where does RTLSDR-Airband fit in?

We make use of the well-designed FFT channelizer and CTCSS detection.

