from numpy import ndarray


class Frame:

    session_id: int
    samples: ndarray
    sample_rate: int

    def __init__(self, session_id: int, fs: int, samples: ndarray):
        self.session_id = session_id
        self.sample_rate = fs
        self.samples = samples

    @property
    def num_samples(self) -> int:
        return len(self.samples)