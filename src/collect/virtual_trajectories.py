
import quaternion

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from utils import G
from scipy.interpolate import interp1d
from scipy.misc import derivative
from imufusion import Ahrs

plt.style.use('pltstyle.mplstyle')

class Trajectory():

    def __init__(self, pos_fun, orient_fun, add_g=True):
        self.idx = 0
        self.dt = .01
        self.g_xyz = quaternion.quaternion(0, 0, 0, G if add_g else 0)
        self.pos_fun = pos_fun
        self.orient_fun = orient_fun

    def generate(self):
        if not hasattr(self, 'times'):
            raise KeyError('Supply times first!')


        N = len(self.times)
        self.virtual_pos = np.empty((N, 3))
        self.virtual_orient = np.empty((N, 3))

        for i, t in enumerate(self.times):
            self.virtual_pos[i] = self.pos_fun(t)
            self.virtual_orient[i] = self.orient_fun(t)


        self.extract_acc()


        if not hasattr(self, 'w_mes'):
            self.w_mes = np.zeros((N,3))
        if not hasattr(self, 'acc_mes'):
            self.acc_mes = np.zeros((N,3))

        return self

    def extract_acc(self):

        def get_d(r, order=2):

            derivs = np.empty(r.shape)
            for xi in range(r.shape[1]):
                f = interp1d(self.times, r[:, xi],
                             kind='cubic',
                             fill_value='extrapolate',
                             assume_sorted=True)
                derivs[:, xi] = np.array([derivative(f, t, dx=self.dt, n=order) for t in self.times])

            return derivs

        # Extract the acceleration in the world coordinates
        self._virtual_acc_xyz = get_d(self.virtual_pos, 2)

        # Extract angular velocities
        self._virtual_w_XYZ = get_d(self.virtual_orient, order=1)

    @property
    def curtime(self):
        return self.idx*self.dt

    @property
    def times(self):
        return self._times

    @times.setter
    def times(self, times):
        self._times = times

    @property
    def trajectory(self):
        return np.hstack((self._times.reshape(-1,1),
                          self.virtual_pos,
                          self.virtual_orient))

    @property
    def orient_xyz(self):
        return quaternion.from_euler_angles(self.virtual_orient)

    @property
    def g_XYZ(self):
        return self.orient_xyz*self.g_xyz*self.orient_xyz.conjugate()

    @property
    def virtual_acc_xyz(self):
        return self._virtual_acc_xyz

    @property
    def virtual_acc_XYZ(self):
        acc_quats = np.hstack((np.zeros(len(self.virtual_acc_xyz)).reshape(-1, 1),
                               self.virtual_acc_xyz))
        acc_quats = quaternion.from_float_array(acc_quats)
        acc_XYZ_quat = self.orient_xyz*acc_quats*self.orient_xyz.conjugate()
        self._acc_XYZ_quat = acc_XYZ_quat

        g_XYZ = quaternion.as_float_array(self.g_XYZ)[:,1:]
        acc_XYZ = quaternion.as_float_array(acc_XYZ_quat)[:,1:]

        return g_XYZ + acc_XYZ


    @property
    def virtual_w_XYZ(self):
        return self._virtual_w_XYZ

    @property
    def acc_XYZ(self):
        return self.virtual_acc_XYZ + self.acc_mes

    @property
    def w_XYZ(self):
        return self.virtual_w_XYZ + self.w_mes

    @property
    def acc_mes(self):
        return self._lin_acc_mes

    @acc_mes.setter
    def acc_mes(self, arr):
        self._lin_acc_mes = arr

    @property
    def w_mes(self):
        return self._w_mes

    @w_mes.setter
    def w_mes(self, arr):
        self._w_mes = arr

def remove_gravity(timedeltas, accs, ws):

    ahrs = Ahrs()

    ag_arr = np.empty(accs.shape)
    i = 0
    for dt, a, w in zip(timedeltas, accs, ws):
        ahrs.update_no_magnetometer(w, a, dt)
        ag_arr[i] = a + ahrs.linear_acceleration*G
        i += 1

    return ag_arr

def add_virtual_signal(df, pos_fun, orient_fun):

    traj = Trajectory(pos_fun, orient_fun)

    acc_mes = df.loc[:, ['ax', 'ay', 'az']].values
    w_mes = df.loc[:, ['wx', 'wy', 'wz']].values
    dtimes = df.loc[:, 'dt'].values

    traj.times = np.cumsum(dtimes)
    traj.acc_mes = remove_gravity(dtimes, acc_mes, w_mes)
    traj.w_mes = w_mes

    traj.generate()

    return traj, acc_mes, w_mes

if __name__ == '__main__':

    vx = 0
    vz = 10
    period = 1

    pos_fun = lambda t: np.array([0, 0, 0*(-1/2*G*t**2)])
    orient_fun = lambda t: np.array([0, np.pi/2*np.sin(t/period*2*np.pi), 0])


    df = pd.read_hdf('data/N=500_f2bce1a4d5.hdf5')
    traj, orig_accs, orig_ws = add_virtual_signal(df, pos_fun, orient_fun)


    _, axarr = plt.subplots(6,1, figsize=(10,8), sharex=True)
    for ax, dat in zip(axarr.ravel(),
                  (orig_accs, traj.acc_XYZ,
                   orig_ws, traj.w_XYZ,
                   traj.virtual_acc_XYZ, traj.virtual_w_XYZ)):
        for i, lab in zip(range(3), ('x', 'y', 'z')):
            ax.plot(traj.times, dat[:, i], label=lab)

    for ax in axarr[:4]:
        ax.legend()
        ax_ = ax.twinx()
        ax_.plot(traj.times, df.sw, lw=.5, color='black')
        ax_.set_yticks([])



    plt.show()






