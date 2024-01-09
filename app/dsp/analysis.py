from .schema import SamplesSequenceSummary
from .utils import dbfs, linear

from typing import Union, Any
import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger("dsp.analysis")


def calculate_rms(samples: np.ndarray,
                  silence_dbfs: Union[float, None] = None,
                  **kwargs: dict[str, Any]) -> float:
    """
    silence_dbfs: specify silence threshold; portions of sample < silence
                  will not count towards RMS.
    """

    # convert to float32
    if samples.dtype == np.int16:
        samples = samples.astype(np.float32) / 32768.

    if not np.issubdtype(samples.dtype, np.floating):
        raise ValueError(f"unsupported samples format ({type(samples.dtype)})")

    samples_selection: np.ndarray = samples

    # retrieve samples greater than silence threshold
    if silence_dbfs is not None:
        silence_threshold = 10 ** (silence_dbfs / 20)
        samples_selection = samples[np.abs(samples) > silence_threshold]

        # Check for NaN or Inf values in non_silent_samples
        if np.isnan(samples_selection).any() or np.isinf(samples_selection).any():
            raise ValueError("Non-silent samples array contains NaN or Inf values.")

        # Check if there are any non-silent samples
        if samples_selection.size == 0:
            return -np.inf  # Return -inf dBFS to indicate silence

        # debugging @ fs=16khz
        fs = kwargs.get('fs', 16000)
        num_silence_samples = len(samples) - len(samples_selection)
        p = round((num_silence_samples / len(samples)) * 100, 1)
        logger.debug(f"silence samples: {num_silence_samples:,} ({p}%)")
        logger.debug(f"{(len(samples) / fs) * (p/100)}")


    # calculate RMS dBFS
    rms = np.sqrt(np.mean(samples_selection ** 2))
    rms_dbfs = round(20 * np.log10(rms), 2)

    return rms_dbfs

# The DC bias represents a constant offset that shifts the entire signal either
# up or down from the zero line.
def calculate_dc_bias(samples: NDArray[np.float32]) -> float:
    if not np.issubdtype(samples.dtype, np.floating):
        raise ValueError("calculate_dc_bias() expected ndarray float32!")
    return np.mean(samples)

def calculate_peak_amplitude(samples: NDArray[np.float32]) -> float:
    if not np.issubdtype(samples.dtype, np.floating):
        raise ValueError("calculate_peak_amplitude() expected ndarray float32!")
    return np.max(np.abs(samples))


def analyze_samples(samples: NDArray, fs: int) -> SamplesSequenceSummary:

    silence_dbfs = -50.

    num_samples = len(samples)

    # convert to float32 for further processing
    if not np.issubdtype(samples.dtype, np.floating):
        samples = samples.astype(np.float32) / 32768.

    summary = SamplesSequenceSummary(
        fs=fs,
        num_samples=num_samples,
        length=num_samples / fs,
        silence_threshold=silence_dbfs
    )

    summary.amplitude_peak = dbfs(calculate_peak_amplitude(samples))
    summary.rms = calculate_rms(samples, fs=fs)
    summary.rms_thresholded = calculate_rms(samples, silence_dbfs, fs=fs)
    summary.dc_bias = calculate_dc_bias(samples)


    return summary