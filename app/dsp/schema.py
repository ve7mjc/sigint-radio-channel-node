from dataclasses import dataclass
from typing import Optional
import os
import sys


@dataclass
class SamplesSequenceSummary:
    fs: int
    num_samples: int
    length: float

    silence_length: Optional[float] = None
    silence_threshold: Optional[float] = None

    rms: Optional[float] = None
    rms_thresholded: Optional[float] = None
    amplitude_peak: Optional[float] = None
    dc_bias: Optional[float] = None

    def report_string(self, ref_id: Optional[str] = None) -> str:

        s = "--------------------------\n"
        s += " Samples Analysis Summary\n"
        s += "--------------------------\n\n"
        if ref_id:
            s += f"{'Reference':>26}: {ref_id}\n"
        s += f"{'Samples':>26}: {self.num_samples:,}\n"
        s += f"{'Length [secs]':>26}: {self.length:,.3f} \n"

        s += "\n"
        s += f"{'RMS [dBFS]':>26}: {self.rms:,} \n"
        s += f"{'RMS Active [dBFS]':>26}: {self.rms_thresholded:,} \n"
        if abs(self.dc_bias) < 0.01:
            s += f"{'DC Bias [float]':>26}: {self.dc_bias:.2e} \n"
        else:
            s += f"{'DC Bias [float]':>26}: {self.dc_bias:.3f} \n"
        s += f"{'Amplitude Peak [dBFS]':>26}: {self.amplitude_peak:,} \n"
        s += "\n"
        return s

    def print(self, ref_id: Optional[str] = None) -> None:
        stdout = sys.stdout.fileno()
        os.write(stdout, self.report_string(ref_id).encode())