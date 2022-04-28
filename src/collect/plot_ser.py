import serial
import imufusion
import hashlib
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib.animation import FuncAnimation
from utils import G, get_ser, set_collect, read_ser, update_df

plt.style.use('pltstyle.mplstyle')

SER = get_ser()
COLLECTT = 15
FREQ = 100
THIST=5
N = int(COLLECTT*FREQ)

df = pd.DataFrame(
    np.zeros((N, 8)),
    columns=['ax', 'ay', 'az', 'wx', 'wy', 'wz', 'dt[mus]', 'sw']
).astype({'dt[mus]': int, 'sw':bool})



fig, (axa, axag, axw, axahrs) = plt.subplots(4, 1, sharex=True, figsize=(10,6))


rpy = ('roll', 'pitch', 'yaw')
la_l = [None]*3
lag_l = [None]*3
lw_l = [None]*3
lahrs_l = [None]*3
line_d = {'color': 'black', 'linewidth':1.}
for i, ls, lab in zip(range(3), ('-', '--', '-.'), ('x', 'y', 'z')):
    la_l[i], = axa.plot([], [], ls, **line_d, label=rf'$a_{lab}$')
    lag_l[i], = axag.plot([], [], ls, **line_d, label=rf'$a_{lab}-g_{lab}$')
    lw_l[i], = axw.plot([], [], ls, **line_d, label=rf'$\omega_{lab}$')
    lahrs_l[i], = axahrs.plot([], [], ls, **line_d, label=rpy[i])

lw_sw = [None]*4
axsw = [None]*4
for i, ax in enumerate((axa, axag, axw, axahrs)):
    axsw[i] = ax.twinx()
    lw_sw[i], = axsw[i].plot([], [], lw=.5, color='black')


a_arr = np.zeros((N, 3))
ag_arr = np.empty((N, 3))
w_arr = np.zeros((N, 3))
ahrs_arr = np.empty((N, 3))
sw_arr = np.zeros(N)
t_arr = np.zeros(N)


axa.set_xlim([-THIST, 0])
for i in range(4):
    axsw[i].set_ylim([-.1, 1.1])
    axsw[i].set_yticks([])
axa.set_ylim([-20, 20])
axag.set_ylim([-4, 4])

axw.set_ylim([-150, 150])
axahrs.set_ylim([-180, 180])
axa.set_title(r'$\mathbf{a}$')
axag.set_title(r'$\mathbf{a}-\mathbf{g}$')
axa.set_ylabel(r'$\frac{m}{s^2}$')
axag.set_ylabel(r'$\frac{m}{s^2}$')
axw.set_title(r'$\omega$')
axw.set_ylabel(r'$\frac{deg}{s}$')
axahrs.set_title('AHRS')
axahrs.set_ylabel('deg')
axahrs.set_xlabel('Time [s]')
axa.legend(loc=3)
axag.legend(loc=3)
axw.legend(loc=3)
axahrs.legend(loc=3)

ahrs = imufusion.Ahrs()

def anim(frame, df):

    while not SER.in_waiting:
        pass

    if SER.in_waiting:
        imu_arr, dt, sw = read_ser(SER)
        dt = float(dt)/1e6

        df = update_df(frame, df, imu_arr, dt, sw)

        a_arr[frame,:] = imu_arr[:3]
        w_arr[frame,:] = imu_arr[3:]
        ahrs.update_no_magnetometer(w_arr[frame, :], a_arr[frame, :], dt)
        ag_arr[frame, :] = a_arr[frame, :]/G+ahrs.linear_acceleration # ahrs.quaternion.to_euler()
        ahrs_arr[frame, :] = ahrs.quaternion.to_euler()

        if frame==0:
            t_arr[frame] = 0
        else:
            t_arr[frame] = t_arr[frame-1]+dt
        sw_arr[frame] = sw

        start = max(0, frame - FREQ*THIST)
        times = t_arr[start:frame]-t_arr[frame]

        for i in range(3):
            la_l[i].set_data(times, a_arr[start:frame, i])
            lag_l[i].set_data(times, ag_arr[start:frame, i])
            lw_l[i].set_data(times, w_arr[start:frame, i])
            lahrs_l[i].set_data(times, ahrs_arr[start:frame, i])

        for i in range(4):
            lw_sw[i].set_data(times, sw_arr[start:frame])

    return *la_l, *lag_l, *lw_l, *lahrs_l, *lw_sw,

set_collect(SER, True)
ani = FuncAnimation(fig,
                    anim,
                    fargs=(df, ),
                    frames=N,
                    interval=.01,
                    blit=True,
                    repeat=False)

plt.show()

# Stop data collection
set_collect(SER, False)

hash_ = hashlib.sha1()
hash_.update(str(time.time()).encode('utf-8'))

df.to_hdf(f'data/N={N}_{hash_.hexdigest()[:10]}.hdf5', 'data')






