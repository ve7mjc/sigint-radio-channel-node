Intercept Two-Way Radio Voice Communications --

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

