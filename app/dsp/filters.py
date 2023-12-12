
from scipy.signal import iirnotch, lfilter
from scipy.signal import butter, filtfilt
from numpy import ndarray


def iir_notch(samples: ndarray, sample_rate: float, notch_freq: float, q: float = 30):
    b, a = iirnotch(notch_freq / (sample_rate / 2), q)
    return lfilter(b, a, samples)


def iir_highpass(samples: ndarray, sample_rate: float,
                 cutoff_frequency: float, order: int = 5):
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff_frequency / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    filtered_data = filtfilt(b, a, samples)
    return filtered_data