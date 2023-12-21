# Concept of Streams

Two-way radio communications begin and end. Filtering realtime streams requires that filter coefficients be carried forward during the lifetime of that particular stream event.

We must signal when the end of these streams are in order to reset/re-init the filters but we must not do so before they are done processing samples.

---

What if we instead created a new class instance for each two-way radio session? We would then process these until they are done?

---

Typical Stream:
  RTLSDR-Airband (UDP 8k frames @ 16 kHz) --> Mumble @ 48kHz

Buffering must be done AFTER all processing, in order to prevent incorrect filter reset timing

----

another option is to pass tuples or structs with the samples and a SESSION_ID alongside

