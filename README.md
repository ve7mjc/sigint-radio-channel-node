# RadioChannel Capture Edge

Facilitate simultaneous acquisition, processing, storage, and distribution of two-way radio communication channels.

## Concept of Operation

User defines stream sources (SDR device(s) for now) and the radio channels. The channel manager will produce an RTLSDR-Airband configuration file, subprocess an rtl_airband binary with provided configuration, and then configure requisite number of UDP channels needed to match RTLSDR-Airband.

Each channel "gates" the stream with either CSQ/CTCSS per rtl_airband, applies multiple audio filters, writes the audio recording to disk as pcm wave, while simultaneously upsampling the streams and passing them to a Mumble server with each channel being a "user".

## Features

* Automatically generate RTLSDR-Airband configuration
  * Permit global, device, and channel specific overrides in the natural format of rtl_airband
* Subprocess/wrap the rtl_airband process with generated configuration file. Waits for rtl_airband to become "ready" and also monitors for premature exit/exception.
* Apply filter chains (notch, low-pass, high-pass, etc) to audio streams
* Write timestamped voice traffic to disk (pcm wav)
* Redirect voice channels to Mumble in realtime
* Ignore nuissance radio clicks/kerchunks from writing to disk (minimum ptt duration)

## Requirements

* Python >= 3.10
* RTLSDR-Airband

## Usage

### Test Development Build

`./setup-dev`

This will configure a Python venv (Virtual Environment) and obtain all of the required third-party Python modules

`./run-dev <config.yaml>`

This will start the application with the supplied configuration file

## Configuration

There may be valid configuration settings which are not covered here.

### Devices

- `type`: `rtlsdr_airband.(rtlsdr|soapysdr)` - instruct RTLSDR-Airband to use RTL-SDR or SoapySDR interface
- `serial` (optional): string to pass to hardware layer for device selection
- `index` (optional): integer to pass to hardware layer for device selection
- `center_freq`: Optional; center frequency to tune SDR to; will be automatically calculated if omitted
- `gain`: passed to rtl_airband

### Mumble

Configuration Section: `mumble:` (Optional)

- `remote_host`:  my.mumblehost.com
- `remote_port`: 3500
- `password`: (Optional) password to supply to Mumble (the auth username will be the LABEL (below))
- `sanitize_usernames`: `(true|false(defaut)) Labels (usernames) with spaces and other characters will error on connection to some Mumble servers. Set to true to sanitize labels/usernames to be compliant.
- `default_channel` (Optional) Voice-Chat-Channel to join for each radio channel. Omit to join root.

### Channels

- `id` (optional): provide an id for this channel which can be referenced elsewhere. Recommended.
- `freq`: frequency of channel in MHz (ie '144.520')
- `label`: string description of channel; used by Mumble, logging, etc
- `designator`: string emission designator (FCC/IC type); examples:
  - `6K00A3E` AM (Double Side-band) - VHF Air Band
  - `11K0F3E` FM Narrow (2.5 KHz) - Commercial Land Mobile Radio, Public Safety
  - `16K0F3E` FM Wide (5.0 KHz) - Marine VHF, Amateur Radio FM VHF
- `ctcss` (optional): `float` CTCSS frequency which will then squelch by rtl_airband and also notch filtered out
- `rtlsdr_airband_overrides` (optional): 'list[str]` list of strings permits injecting of RTLSDR-Airband configuration directives.


### Example Config

```yaml
global_overrides:
#   - "fft_size = 1024;"
#   - "tau = 600;"

listen_port_base: 6100

mumble:
  remote_host: mumble-server.example.com
  remote_port: 3500
  default_channel: Radio Channels

devices:
  - id: rtlsdr_34
    type: rtlsdr_airband.rtlsdr
    serial: "00000034"
    gain: 28
    center_freq: 119.365

channels:
  - id: cyvr-tower-south
    freq: 118.700
    label: Vancouver Tower (South)
    designator: 6K00A3E
    rtlsdr_airband_overrides:
     - "squelch_threshold = -50;"

  - id: cyvr-tower-north
    freq: 119.550
    label: Vancouver Tower (North)
    designator: 6K00A3E

  - id: cyyj-tower-outer
    freq: 119.100
    label: Victoria (CYYJ) Tower (Outer)
    designator: 6K00A3E
```

## RTLSDR-Airband Channel Listeners

We configure RTLSDR-Airband to output via UDP packets. The output format is an 8000 bytes datagram with 32-bit float samples (2,000 samples) at 16,000 samples/sec. Each datagram contains 125 msec of audio. The datagrams appear to always be 8000 bytes, with the final datagram being padded with 0x00 bytes.

RTLSDR-Airband falls short in a few ways:

* Saves only MP3 format
* Filter options are limited - eg. only one notch per channel and the high/low-pass filters are only available under certain conditions.

# Where does RTLSDR-Airband fit in?

We make use of the well-designed FFT channelizer and CTCSS detection.



# Dependencies

## Pymumble_py3

https://github.com/azlux/pymumble/tree/pymumble_py3

### Problems with pymumble

- Project is abandoned (2024-05-14) ([source](https://github.com/azlux/pymumble/commit/a560e6013dfbccb3666ce8756e1ca6b790bf05c8))
- Does not work with Python >= 3.12 (SSL Errors)
- Does not support UDP


## Developmment

### Remote / Embedded Development

In the case of editing a codebase that is mounted remotely (ie. sshfs, etc) and you desire IDE type hinting or code completion - it is recommended to create a local Python VENV environment for the purpose of code completion, etc.

```
cd {this-project-dir}

# check version
python --version

python -m venv /some/local/path
ln -s /some/local/path local-venv/

source ./local-venv/bin/activate
```
