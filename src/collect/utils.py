import struct
import serial

import logging
import numpy as np
import pandas as pd

LOG = logging.getLogger()
BAUD = 115200
NBYTES = 28
G = 9.81
SER = serial.Serial(
            port='/dev/ttyACM0',
            baudrate=BAUD,
            timeout=.01,
            write_timeout=0,
        )


def unpack(bytearr : bytearray,
           to : str = 'f'):
    if to not in ['f', 'H']:
        raise KeyError(f'Only floats "f" and ints "H" supported. You gave : {to}')

    return struct.unpack(to, bytearr)[0]



def set_collect(ser : serial.Serial,
                collect : bool = True) -> None:
    """
    Stop the data collection.
    """
    LOG.info(f'Collect state --> {collect}')
    mode = (int(collect)).to_bytes(1, byteorder='big')
    ser.write(mode)

def read_ser(ser : serial.Serial) -> tuple[np.ndarray, int, bool]:
    bytes_ = ser.read(NBYTES)
    if bytes_[-1:] != b'\x0A':
        warnings.formatwarning('Somehow crappy readings received.')
        ser.flushInput()
        return None


    return format_read(bytearr=bytes_)


def format_read(bytearr : bytearray) -> tuple[np.ndarray, int, bool]:

    imu_arr = np.zeros(6)
    for i in range(6):
        imu_arr[i] = unpack(bytearr[i*4:(i+1)*4], 'f')
    imu_arr[:3] *= G


    dt = int(unpack(bytearr[24:26], 'H'))
    sw =  bool(bytearr[26])

    return imu_arr, dt, sw

def update_df(idx : int,
              df : pd.DataFrame,
              imu_arr : np.ndarray,
              dt : int,
              sw : bool) -> pd.DataFrame:


    df.loc[idx, ['ax', 'ay', 'az']] = imu_arr[:3]*G
    df.loc[idx, ['wx', 'wy', 'wz']] = imu_arr[3:]
    df.loc[idx, 'dt[mus]'] = dt
    df.loc[idx, 'sw'] = sw

    return df

