
# Many public safety pagers and control systems use audio tones to activate.
# The most common type is two tones sent in sequence.
#   - Two-Tone Paging or Two-Tone Sequential.

# Silence detection
# Example file: fire-nanaimo-pagers_20231226T131717.wav
#  manualy sliced out silence periods: 16.6 seconds (remaining)
#  measure_rms method with -50. dBFS silence threshold = 9.1 S
#  Reasonable considering there is inter-syllable silence


"""
Frequency Resolution:

Frequency Resolution = Sampling Rate / Window Length

Time Resolution:

Window Length: Dictates the smallest feature (in time) that can be accurately
captured.

Hop Length: The number of samples by which the window is advanced during the
STFT process. It's calculated as window_length - overlap. The hop length
determines how frequently the signal is sampled for the STFT and affects the
smoothness of the time representation.

If we define time resolution as the ability to distinguish two successive
events, it's closely related to the hop length. The time between successive
windows, or the effective time resolution, is given by:

Time Resolution (effective) = Hop Length / Sampling Rate
                            = (Window Length - Overlap) / Sampling Rate

However, if we consider time resolution as the ability to accurately capture the
duration of features in the signal, it's more closely related to the window
length:

Time Resolution (capture)   = Window Length / Sampling Rate

"""





from app.dsp.schema import SamplesSequenceSummary
from app.dsp.analysis import analyze_samples
from app.dsp.utils import dbfs, linear

from app.radio.tone_coding.two_tone_sequential import code_from_freqs, TwoToneSequence


import numpy as np
import scipy.fft
from scipy.fft import rfft, rfftfreq
import scipy.io.wavfile
from scipy.signal import stft, find_peaks
import matplotlib.pyplot as plt

import numpy as np
from numpy.typing import NDArray
import scipy.fft

from pathlib import Path
import os
from dataclasses import dataclass, field
import logging
from typing import Union, Any, Optional


logger = logging.getLogger(__name__)


def get_captures(target_folder: str, pattern: str = "*.wav") -> list[str]:
    folder_path = Path(target_folder)
    captures = [str(file.relative_to(folder_path)) for file in folder_path.glob(pattern)]
    return captures

def read_capture(file_name: str) -> tuple[int, np.ndarray]:
    sample_rate, audio_samples = scipy.io.wavfile.read(file_name)
    return sample_rate, audio_samples

def apply_fft(audio_samples: np.ndarray) -> np.ndarray:
    fft_output = scipy.fft.fft(audio_samples)
    return np.abs(fft_output)

def detect_tones(fft_output: np.ndarray, sample_rate: int) -> np.ndarray:
    frequencies = scipy.fft.fftfreq(len(fft_output), 1 / sample_rate)
    threshold = np.max(fft_output) / 2  # Example threshold
    peak_frequencies = frequencies[fft_output > threshold]
    return peak_frequencies


def process_block(block: np.ndarray, sample_rate: int) -> None:
    fft_output = np.abs(scipy.fft.fft(block))
    frequencies = scipy.fft.fftfreq(len(block), 1 / sample_rate)
    threshold = np.max(fft_output) / 2  # Example threshold
    peak_frequencies = frequencies[fft_output > threshold]
    print("Detected Tones:", peak_frequencies[peak_frequencies > 0])  # Print positive frequencies

# def real_time_processing(block_duration: float = 0.04) -> None:
#     sample_rate = 44100  # Standard sample rate
#     block_size = int(sample_rate * block_duration)
#     with sd.InputStream(callback=lambda indata, frames, time, status: process_block(indata[:, 0], sample_rate),
#                         blocksize=block_size,
#                         samplerate=sample_rate,
#                         channels=1):
#         print("Starting real-time processing...")
#         input("Press Enter to stop...")


# file_name = "your_audio_file.wav"  # Replace with your audio file
# sample_rate, audio_samples = read_audio(file_name)
# fft_output = apply_fft(audio_samples)
# tones = detect_tones(fft_output, sample_rate)


@dataclass
class ToneDetection:
    frequency: float
    amplitude: float
    sample_start: int
    sample_end: Optional[int] = None
    sample_soft_end: Optional[int] = None
    freq_centers: list[float] = field(default_factory=list)
    duration: Optional[float] = None

class ToneDetector:

    fs: float

    tone_min_samples: float
    tone_min_dbfs: float
    tone_min_amplitude: float

    tone_end_tolerance: int

    samples_processed: int

    tones: list[ToneDetection]
    active_tones: dict[str, ToneDetection]

    window_length: int
    overlap: int

    def __init__(self, sampling_rate: int, tone_min_dbfs: float,
                 tone_min_length: float, **kwargs: dict):

        self.fs = sampling_rate

        self.tone_min_dbfs = tone_min_dbfs
        self.tone_min_amplitude = linear(tone_min_dbfs)

        self.tone_min_samples = int(sampling_rate * tone_min_length)

        # defaults
        self.tones = []
        self.active_tones = {}
        self.samples_processed = 0

        # SFFT
        self.window_length = 4096
        self.overlap = self.window_length * 0.5

    def print_parameters(self):

        print("ToneDetector Parameters:")
        print(f"  tone_min_ampl: {self.tone_min_amplitude:,.4f} ({self.tone_min_dbfs} dBFS)")

        freq_res = self.fs / self.window_length
        time_res_cap = self.window_length / self.fs
        time_res_eff = (self.window_length - self.overlap) / self.fs

        print(f"  frequency_resolution: {freq_res:,} Hz")
        print(f"  time_resolution_capture: {time_res_cap:,.3f} sec")
        print(f"  time_resolution_effective: {time_res_eff:,.3f} sec")
        print()

    def _register_detection(self, detection: ToneDetection):
        length_samples = detection.sample_end - detection.sample_start
        detection.duration = length_samples / self.fs
        if length_samples > self.tone_min_samples:
            self.tones.append(detection)

        # was experimenting whether I could get multiple frequency bin centers
        # print(detection.freq_centers)

    # Detect Peaks in Each Segment: In each STFT segment, detect the peaks as
    # you would in the full FFT. This will give you the frequencies and their
    # amplitudes for each time segment.

    """
    Window Length (window_length): Determines the frequency resolution.
     - A longer window provides better frequency resolution (narrower
       frequency bins) but worse time resolution.
     - A shorter window offers better time resolution but broader frequency
     - bins, which might not distinguish closely spaced frequencies well.

    Overlap (overlap): Determines how much each successive window overlaps with the previous one.
     - Higher overlap can lead to smoother and more continuous time
       representation, especially useful in dynamic signal analysis.
     - Overlap is typically a fraction of the window length (common choices
       are 25%, 50%, or 75%).
"""

    # Track Tone Occurrences Over Time: For each detected frequency, track its
    # presence over consecutive segments. You can start a ToneDetection instance
    # when a frequency first appears and end it (set stop_sample) when it
    # disappears.

    # Handle Overlap and Windows in STFT: STFT involves windowing and
    # overlapping segments. You'll need to consider these factors to accurately
    # calculate sample_start and stop_sample.

    def process_block(self, samples: NDArray[np.float32]) -> None:

        tone_tol = 5  # hz
        time_tol = 0.005  # 5 ms to permit glitching?
        self.tone_end_tolerance = self.fs * time_tol

        # convert to float32 if int16/int32
        if not np.issubdtype(samples.dtype, np.floating):
            samples = samples.astype(np.float32) / 32768.

        # Perform Short-Time Fourier Transform (STFT): Instead of using FFT on
        # the entire signal, use STFT. STFT divides the signal into shorter
        # segments and performs FFT on each segment. This gives you frequency
        # information localized in time.

        hop_length = self.window_length - self.overlap

        # Perform STFT
        f, t, Zxx = stft(samples, fs=self.fs, nperseg=self.window_length,
                         noverlap=self.overlap)

        amplitudes = np.abs(Zxx)

        for idx, time in enumerate(t):
            segment_start = int(idx * hop_length)

            freq_bin = amplitudes[:, idx]
            peaks, _ = find_peaks(freq_bin, height=self.tone_min_amplitude)

            for peak in peaks:
                frequency = f[peak]
                amplitude = freq_bin[peak]

                # determine if known
                active_tone_id: Union[int, None] = None
                for tone_id in self.active_tones:
                    if abs(frequency - tone_id) < tone_tol:
                        active_tone_id = tone_id

                # append freq if known
                if active_tone_id:
                    self.active_tones[active_tone_id].freq_centers.append(frequency)

                # this tone is new
                if active_tone_id is None:
                    tone = ToneDetection(
                            frequency=frequency,
                            amplitude=amplitude,
                            sample_start=segment_start
                        )
                    self.active_tones[round(frequency)] = tone


                # print(f"peak {frequency} @ {dbfs(amplitude):.1f} dBFS")

                # # match whether tone is active
                # matched_tone: Union[int, None] = None
                # for active_tone in range(self.active_tones):
                #     pass

                # if matched_tone is None:
                #     tone = ToneDetection(frequency, amplitude, segment_start)
                #     self.active_tones.append()

                # else:
                #     # Update existing tone
                #     ongoing_tones[frequency].amplitude = amplitude  # Update amplitude

            # establish if any tones have ended
            tones_ended = []
            for tone_id, active_tone in self.active_tones.items():

                active: bool = False  # assume tone ended until proven otherwise

                for peak in peaks:
                    frequency = f[peak]

                    if abs(frequency - active_tone.frequency) < tone_tol:
                        active = True

                # Mark a tone for ended but filtered
                if not active:

                    if active_tone.sample_soft_end is None:
                        active_tone.sample_soft_end = segment_start

                    elif (segment_start - active_tone.sample_soft_end) > self.tone_end_tolerance:
                        active_tone.sample_end = active_tone.sample_soft_end
                        self._register_detection(active_tone)
                        tones_ended.append(tone_id)

            for tone_id in tones_ended:
                del self.active_tones[tone_id]


                # if active_tone.frequency not in f[peaks]:
                #
                #     self.tones.append(active_tone)
                # del active_tone

        #     # Remove ended tones from ongoing tracking
        #     for freq in ended_tones:
        #         del ongoing_tones[freq]

        # # Add any remaining ongoing tones as they did not end within the signal
        # for tone in ongoing_tones.values():
        #     tone.stop_sample = len(samples)
        #     self.tones.append(tone)


        # Perform Fourier Transform
        freq_amplitudes = np.abs(rfft(samples))
        freqs = rfftfreq(samples.size, 1 / self.fs)

        # Find peaks above the noise threshold
        # peaks = np.where(freq_amplitudes > self.noise_threshold)[0]

        # Find peaks
        peaks, _ = find_peaks(freq_amplitudes, height=self.tone_min_amplitude)

        # Filter peaks based on bandwidth (if needed)
        # Example: peaks = [p for p in peaks if lower_bound <= freqs[p] <= upper_bound]

        # Extract frequency and amplitude of peaks
        peak_freqs = freqs[peaks]
        peak_amps = freq_amplitudes[peaks]



        # current_tones = set()
        # for peak in peaks:
        #     frequency = freqs[peak]
        #     current_tones.add(frequency)

        #     if frequency not in self.active_tones:
        #         self.active_tones[frequency] = self.samples_processed - len(samples)

        # # End tones that are no longer present
        # for tone, start_sample in list(self.active_tones.items()):
        #     if tone not in current_tones:
        #         tone_duration_samples = self.samples_processed - start_sample
        #         tone_duration_seconds = tone_duration_samples / self.fs
        #         print(f"Tone: {tone:.2f} Hz, Duration: {tone_duration_seconds:.2f} seconds")
        #         del self.active_tones[tone]

        # record our work
        self.samples_processed += len(samples)


    def finalize(self):
        pass
        # End any remaining active tones
        # for tone, start_sample in self.active_tones.items():
        #     tone_duration_samples = self.samples_processed - start_sample
        #     tone_duration_seconds = tone_duration_samples / self.fs
        #     print(f"Tone: {tone:.2f} Hz, Duration: {tone_duration_seconds:.2f} seconds")

        # self.active_tones.clear()


# sample_rate = 44100  # Standard sample rate
# block_duration = 0.04  # 40 milliseconds
# noise_threshold = 0.5  # Example threshold, adjust based on your audio
# detector = ToneDetector(sample_rate, block_duration, noise_threshold)
# real_time_processing(detector)
#

if __name__ == "__main__":

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    # load up dispatch recordings
    captures_path = "/opt/data/radio_channels/fire-nanaimo-pagers"
    captures_path = "/opt/data/test_pages/nfr"


    for file in get_captures(captures_path):
        file_path = os.path.join(captures_path, file)
        if "_raw" in file:
            continue

        print(f"\r\n --- {file}:")

        fs, samples = read_capture(file_path)

        # summary = analyze_samples(samples, 16000)
        # summary.print(file)

        min_length = 0.1
        tone_min_dbfs = -25.

        detector = ToneDetector(fs, tone_min_dbfs, min_length)
        # detector.print_parameters()
        detector.process_block(samples)
        detector.finalize()

        for tone in detector.tones:
            start_time = tone.sample_start / fs
            tone_length = (tone.sample_end - tone.sample_start) / fs
            # print(f" - {start_time:,.3f}: {round(tone.frequency):,} {dbfs(tone.amplitude)} dBFS [{tone_length:,.3f}]")


        if len(detector.tones) >= 2:
            # pass to tone coding decoder
            tone_a = detector.tones[0]
            if tone_a.duration < 0.75 or tone_a.duration > 1.2:
                logger.debug(f"skipping tone 1 duration '{tone_a.duration}'")
                continue

            tone_b = detector.tones[1]
            if tone_b.duration < 2.4 or tone_b.duration > 3.2:
                logger.debug(f"skipping tone 1 duration '{tone_b.duration}'")
                continue

            code = code_from_freqs(tone_a.frequency, tone_b.frequency)
            print(f"poss detection: {code.group} {code.id} ({code.tone_1.freq}, {code.tone_2.freq})")

        # break

        # block_size = int(detector.sample_rate * detector.block_duration)
        # with sd.InputStream(callback=lambda indata, frames, time, status: detector.process_block(indata[:, 0]),
        #                     blocksize=block_size,
        #                     samplerate=detector.sample_rate,
        #                     channels=1):
        #     print("Starting real-time processing...")
        #     input("Press Enter to stop...")


        # process_block(samples, fs)
        #
