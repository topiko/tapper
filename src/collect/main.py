import serial
import time
import warnings
import logging
import struct

import numpy as np
import pandas as pd
from utils import set_collect, read_ser, update_df
from utils import BAUD, NBYTES, G, SER

LOG = logging.Logger(__name__)

COLLECTT = 1
N = 100*COLLECTT

mode = False
set_collect(SER, mode)

df = pd.DataFrame(
    np.zeros((N, 8)),
    columns=['ax', 'ay', 'az', 'wx', 'wy', 'wz', 'dt[mus]', 'sw']
).astype({'dt[mus]': int, 'sw':bool})

tup = time.time()
if __name__ == "__main__":
    while True:
        if (time.time()-tup) > COLLECTT:
            mode = not mode
            set_collect(SER, mode)
            tup = time.time()
            idx = 0

        if SER.in_waiting:

            df = update_df(idx, df, *read_ser(SER))

            print(df.loc[idx, :])
            idx += 1



