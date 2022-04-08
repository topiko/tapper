import serial

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import hashlib
import time

from matplotlib.animation import FuncAnimation
from utils import SER, collect_start_stop, read_ser, update_df

plt.style.use('pltstyle.mplstyle')

COLLECTT = 20
FREQ = 100
N = COLLECTT*FREQ

df = pd.DataFrame(
    np.zeros((N, 8)),
    columns=['ax', 'ay', 'az', 'wx', 'wy', 'wz', 'dt[mus]', 'sw']
).astype({'dt[mus]': int, 'sw':bool})



fig, (axa, axw) = plt.subplots(2, 1, sharex=True, figsize=(10,6))

la_l = [None]*3
lw_l = [None]*3
for i, ls, lab in zip(range(3), ('-', '--', '-.'), ('x', 'y', 'z')):
    la_l[i], = axa.plot([], [], ls, color='black', label=rf'$a_{lab}$')
    lw_l[i], = axw.plot([], [], ls, color='black', label=rf'$\omega_{lab}$')

lw_sw = [None]*2
axsw = [None]*2
for i, ax in enumerate((axa, axw)):
    axsw[i] = ax.twinx()
    lw_sw[i], = axsw[i].plot([], [], lw=.5, color='black')


a_arr = np.zeros((N, 3))
w_arr = np.zeros((N, 3))
sw_arr = np.zeros(N)
t_arr = np.zeros(N)


axa.set_xlim([-5, 0])
for i in range(2):
    axsw[i].set_ylim([-.1, 1.1])
    axsw[i].set_yticks([])
axa.set_ylim([-20, 20])
axw.set_ylim([-150, 150])
axa.set_title(r'$\mathbf{a}$')
axa.set_ylabel(r'$\frac{m}{s^2}$')
axw.set_title(r'$\omega$')
axw.set_ylabel(r'$\frac{deg}{s}$')
axw.set_xlabel('Time [s]')
axa.legend(loc=3)
axw.legend(loc=3)

def anim(frame, df):

    while not SER.in_waiting:
        pass

    if SER.in_waiting:
        imu_arr, dt, sw = read_ser(SER)
        df = update_df(frame, df, imu_arr, dt, sw)
        a_arr[frame,:] = imu_arr[:3]
        w_arr[frame,:] = imu_arr[3:]
        if frame==0:
            t_arr[frame] = 0
        else:
            t_arr[frame] = t_arr[frame-1]+float(dt)/1e6
        sw_arr[frame] = sw

        times = t_arr[:frame]-t_arr[frame]
        for i in range(3):
            la_l[i].set_data(times, a_arr[:frame, i])
            lw_l[i].set_data(times, w_arr[:frame, i])

        for i in range(2):
            lw_sw[i].set_data(times, sw_arr[:frame])

    return *la_l, *lw_l, *lw_sw,

collect_start_stop(SER, True)
ani = FuncAnimation(fig,
                    anim,
                    fargs=(df, ),
                    frames=N,
                    interval=.01,
                    blit=True,
                    repeat=False)

plt.show()

# Stop data collection
collect_start_stop(SER, False)

hash_ = hashlib.sha1()
hash_.update(str(time.time()).encode('utf-8'))

df.to_hdf(f'data/N={N}_{hash_.hexdigest()[:10]}.hdf5', 'data')





