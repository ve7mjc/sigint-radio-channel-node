from typing import Union


def channel_closest_center(channels: list[Union[int,float]]) -> Union[int,float]:
    """
    supports both int and float; returns the same as input
    """
    if len(channels) == 0:
        return None
    elif len(channels) == 1 or len(channels) == 2:
        return channels[0]
    else:
        chan_max = max(channels)
        chan_min = min(channels)
        freq_center = chan_min + ((chan_max - chan_min) / 2)

        # find channel with least distance from center
        chan_least = None
        dist_least = None
        for channel in channels:
            dist = abs(channel - freq_center)

            if chan_least is None or dist < dist_least:
                chan_least = channel
                dist_least = dist

    return chan_least

def bandwidth_required(channel_frequencies: list[float],
                       channel_width: int) -> int:

        # frequencies are float mhz
        freq_min_hz = int(min(channel_frequencies) * 1e6)
        freq_max_hz = int(max(channel_frequencies) * 1e6)

        return (freq_max_hz - freq_min_hz) + channel_width

