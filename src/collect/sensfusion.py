import numpy as np
import pandas as pd
import quaternion as qt

import matplotlib.pyplot as plt

from imufusion import Ahrs
from ahrs.filters import Mahony as Mahony2
from ahrs.filters import Madgwick
from qutils import q2eul, eul2q, q2rotmat

plt.style.use('pltstyle.mplstyle')


class Mahony():

    def __init__(self):
        self._qhat = eul2q(0,0,0)
        self.bhat = np.zeros(3)
        self.g = np.array([0,0,-1])
        self.kp = 1
        self.ki = .3

    def update(self, acc, omega, dt):


        if not np.isclose(np.linalg.norm(acc), 1):
            acc /= np.linalg.norm(acc)

        v = acc
        R = qt.as_rotation_matrix(self.qhat)
        vhat =  -R.T@self.g

        w_mes = np.cross(v, vhat)


        # P quaternion:
        p = qt.quaternion(0)
        p.vec = omega - self.bhat + self.kp*w_mes


        # Q dot:
        qhatdot = 1/2. * self._qhat*p

        # bhat dot:
        bhatdot = -self.ki*w_mes

        # Update:
        self._qhat += dt*qhatdot

        #assert np.isclose(self.qhat.norm(), 1)

        self._qhat /= self.qhat.norm()

        self.bhat += dt*bhatdot

    @property
    def qhat(self) -> qt.quaternion:
        return self._qhat

if __name__ == '__main__':
    df = pd.read_hdf('data/N=500_d54d371192.hdf5')


    N = 600
    acc_arr = df.loc[:, ['ax', 'ay', 'az']].values[:N]
    omega_arr = df.loc[:, ['wx', 'wy', 'wz']].values[:N]
    times = np.cumsum(df.loc[:, 'dt'].values[:N])

    mahony = Mahony()
    mahony2 = Mahony2()
    madgwick = Madgwick()
    ahrs = Ahrs()

    mah_arr = np.empty((len(times), 3))
    mad_arr = mah_arr.copy()
    mah2_arr = mah_arr.copy()
    ahrs_arr = mah_arr.copy()

    i = 0
    mah2_prev = np.array([1.,0,0,0])
    madgwick_prev = np.array([1.,0,0,0])
    for acc, omega in zip(acc_arr, omega_arr):
        dt = df.loc[i, 'dt']

        # Externel AHRS...
        ahrs.update_no_magnetometer(omega, acc, dt)

        acc /= np.sqrt((acc**2).sum())
        omega = omega/180*np.pi

        # Local mahony
        mahony.update(acc, omega, dt)

        # External Mahony
        mahony2.Dt = dt #100 #new_sample_rate
        mah2_prev = mahony2.updateIMU(mah2_prev, gyr=omega, acc=acc)

        # External madwick
        madgwick.Dt = dt
        madgwick_prev = madgwick.updateIMU(madgwick_prev, gyr=omega, acc=acc)

        mah_arr[i] = q2eul(mahony.qhat)/np.pi*180
        ahrs_arr[i] = ahrs.quaternion.to_euler()
        mah2_arr[i] = q2eul(qt.quaternion(*mah2_prev))/np.pi*180
        mad_arr[i] = q2eul(qt.quaternion(*madgwick_prev))/np.pi*180

        i += 1



    _, (ax1, ax2, ax3, ax4) = plt.subplots(4,1, sharex=True, figsize=(10,6))
    line_d = {'color': 'black', 'linewidth':1.}
    for i, lab, ls in zip(range(3), ('pitch', 'roll', 'yaw'), ('-', '--', '-.')):
        ax1.plot(times, mah_arr[:, i], ls, **line_d, label=lab)
        ax2.plot(times, mah2_arr[:, i], ls, **line_d, label=lab)
        ax3.plot(times, ahrs_arr[:, i], ls, **line_d, label=lab)
        ax4.plot(times, mad_arr[:, i], ls, **line_d, label=lab)

    ax4.set_title('Madwick')
    ax3.set_title('Ahrs')
    ax1.set_title('My Mahony')
    ax2.set_title('External Mahony')
    ax1.legend()
    ax4.set_xlabel('Time [s]')
    plt.show()

