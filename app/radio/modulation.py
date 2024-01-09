from enum import Enum

# "narrow" = 2.5kHz max deviation with 3.125kHz max modulation frequency --> 11.25kHz bandwidth
# The emission designator is 11k0f3e.
# This will fit in 12.5kHz-spaced channels, hence the "12.5kHz" channel naming.

# "wide" = 5kHz max deviation with 3kHz max modulation frequency --> 16kHz bandwidth
# The emission designator is 16k0f3e.

# Bottom line is
#   25 kHz spaced channel = "wide" (16k0f3e); and
#   12.5 kHz spaced channel = "narrow" (11k0f3e).


class ModulationType:
    AM = "am"
    FM = "fm"
    C4FM = "c4fm"
