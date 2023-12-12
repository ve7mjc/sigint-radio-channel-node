from .filters import iir_notch
from numpy import ndarray

def remove_ctcss(samples: ndarray, sample_rate: float, ctcss_freq: float):

    # Calculate Q factor
    f0 = ctcss_freq
    bandwidth_hz = 20
    q_factor = f0 / bandwidth_hz

    return iir_notch(samples, sample_rate, ctcss_freq, q_factor)
