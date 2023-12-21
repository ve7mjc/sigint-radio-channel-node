from typing import Union, Optional
from enum import Enum

from scipy.signal import iirnotch, sosfilt, sosfilt_zi, butter, filtfilt, tf2sos  # lfilter
from scipy.signal import butter, filtfilt
from numpy import ndarray


class FilterType(Enum):
    HIGHPASS = 0
    LOWPASS = 1
    NOTCH = 2

class StreamingFilter:

    filter_type: FilterType
    sampling_freq: int
    zi: Union[ndarray, None]
    order: Optional[int]
    freq: Optional[float]
    sos: Optional[ndarray]

    def __init__(self, filter_type: FilterType, sampling_freq: int,
                 order: Optional[int] = None,
                 freq: Optional[float] = None):

        self.filter_type = filter_type
        self.order = order
        self.freq = freq
        self.sampling_freq = sampling_freq
        self.zi = None
        self.sos = None

        if filter_type == FilterType.HIGHPASS:
            self._init_highpass()
        elif filter_type == FilterType.LOWPASS:
            self._init_lowpass()
        elif filter_type == FilterType.NOTCH:
            self._init_notch()
        else:
            raise ValueError(f"no filter init method written for {filter_type}")

        self.reset()

    def _init_highpass(self):
        Wn = self.freq / (self.sampling_freq / 2)  # Normalize the frequency
        self.sos = butter(self.order, Wn, btype='highpass', output='sos')

    def _init_lowpass(self):
        Wn = self.freq / (self.sampling_freq / 2)  # Normalize the frequency
        self.sos = butter(self.order, Wn, btype='lowpass', output='sos')

    def _init_notch(self):
        Q = 30
        w0 = self.freq/(self.sampling_freq/2)
        # normalized scalar that must satisfy 0 < w0 < 1,
        # with w0 = 1 corresponding to half of the sampling frequency
        b, a = iirnotch(w0=w0, Q=Q)
        self.sos = tf2sos(b, a)

    def filter(self, samples: ndarray) -> ndarray:
        filtered, self.zi = sosfilt(self.sos, samples, zi=self.zi)
        return filtered

    def reset(self):
        initial_input_value = 0
        self.zi = sosfilt_zi(self.sos) * initial_input_value

