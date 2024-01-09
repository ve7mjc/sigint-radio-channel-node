from typing import Union

import numpy as np


def dbfs(value: Union[float, int], fullscale: Union[float, int] = 1.0,
            round_ndigits: Union[int, None] = 2):

    dbfs = 20 * np.log10(value)
    if round_ndigits:
        dbfs = round(dbfs, round_ndigits)

    return dbfs

def linear(dbfs: float, full_scale: Union[float, int] = 1.0) -> float:
    return full_scale * 10 ** (dbfs / 20)
