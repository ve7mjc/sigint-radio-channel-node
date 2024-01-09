# RTLSDR-Airband

Scraps of notes/observations.

## Bandwidth Channel

bandwidth channel option enables lowpass filter that operates on the channelized I/Q signal (before demodulation). The result is twofold:

file and icecast outputs have their own lowpass and highpass filters which are enabled by default and perform audio filtering at the MP3 compression stage. If bandwidth is enabled, the signal is effectively filtered twice, which might cause overly high attenuation of higher tones. Consider disabling output filters in this case. See Audio filters in MP3 outputs for details.

## CTCSS

## Notch Filtering

NOTE: If ctcss is enabled the notch filtering is done after squelch processing so the output audio is filtered withough impacting squelch.

Set the notch channel option to the frequency of the interfering tone that you want to cancel out

# UDP Output Observations

* Every packet contains 8,000 bytes exactly (tested with NFM and 16 kHz)
  * This must mean that some padding is happening!
