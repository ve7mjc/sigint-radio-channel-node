from samplerate import Resampler
from numpy import ndarray

class StreamResampler:

    rate_in: int
    rate_out: int
    ratio: float

    _resampler: Resampler

    def __init__(self, rate_in: int, rate_out: int):

        self.rate_in = rate_in
        self.rate_out = rate_out

        self.ratio = self.rate_out / self.rate_in

        converter = 'sinc_best'
        self._resampler = Resampler(converter, channels=1)

    def process(self, samples: ndarray) -> ndarray:
        resampled = self._resampler.process(samples, self.ratio)
        return resampled

    def reset(self):
        self._resampler.reset()

