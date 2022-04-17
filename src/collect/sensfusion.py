import numpy as np
import pandas as pd
import quaternion as qt

import matplotlib.pyplot as plt

from imufusion import Ahrs
from ahrs.filters import Mahony as Mahony2
from ahrs.filters import Madgwick
from qutils import q2eul, eul2q, q2rotmat

def vvt(v1 : np.ndarray,
        v2 : np.ndarray) -> np.ndarray:
    return v1.reshape(3,1)@v2.reshape(1,3)

def vtv(v1 : np.ndarray, v2 : np.ndarray) -> float:
    return v1.dot(v2)

def vex(A : np.ndarray) -> np.ndarray:
    return np.array([-A[1,2], A[0,2], -A[0,1]])

def q_prod(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    pq = np.zeros(4)
    pq[0] = p[0]*q[0] - p[1]*q[1] - p[2]*q[2] - p[3]*q[3]
    pq[1] = p[0]*q[1] + p[1]*q[0] + p[2]*q[3] - p[3]*q[2]
    pq[2] = p[0]*q[2] - p[1]*q[3] + p[2]*q[0] + p[3]*q[1]
    pq[3] = p[0]*q[3] + p[1]*q[2] - p[2]*q[1] + p[3]*q[0]
    return pq



def qprod(q1 : qt.quaternion,
          q2 : qt.quaternion) -> qt.quaternion:

    s1 = q1.real
    s2 = q2.real
    v1 = q1.vec
    v2 = q2.vec

    r = s1*s2 - vtv(v1, v2)
    i = s1*v2 + s2*v1 + np.cross(v1, v2)

    return qt.quaternion(r, i[0], i[1], i[2])

class Mahony():

    def __init__(self, bias=np.zeros(3)):
        self._qhat = qt.from_euler_angles(0,0,0)
        self.bhat = bias #np.zeros(3)

        self.g = np.array([0,0,1])
        self.kp = 1
        self.ki = .3

    def update(self, acc, omega, dt):


        """
        if omega is None or not np.linalg.norm(omega) > 0:
            return q
        Omega = np.copy(omega)
        a_norm = np.linalg.norm(acc)
        if a_norm > 0:
            R = qt.as_rotation_matrix(self.qhat)
            v_a = R.T@np.array([0.0, 0.0, 1.0])     # Expected Earth's gravity
            # ECF
            omega_mes = np.cross(acc/a_norm, v_a)   # Cost function (eqs. 32c and 48a)
            bDot = -self.ki*omega_mes                   # Estimated change in Gyro bias
            self.bhat += bDot * dt                          # Estimated Gyro bias (eq. 48c)
            Omega = Omega - self.bhat + self.kp*omega_mes  # Gyro correction
        p = np.array([0.0, *Omega])
        qDot = 0.5*q_prod(qt.as_float_array(self.qhat), p)                     # Rate of change of quaternion (eqs. 45 and 48b)
        qDot = qt.quaternion(*qDot)

        self._qhat += qDot*dt                                # Update orientation
        self._qhat /= self.qhat.norm()                      # Normalize Quaternion (Versor)
        #return q
        """

        if not np.isclose(np.linalg.norm(acc), 1):
            acc /= np.linalg.norm(acc)



        v = acc
        R = qt.as_rotation_matrix(self.qhat)
        print(R)
        print(q2rotmat(self.qhat))
        vhat =  R.T@self.g

        #w_mes = -vex(vvt(v, vhat) - vvt(vhat, v))
        w_mes = np.cross(v, vhat) #== w_mes; print(w_mes- w_mes2)


        # P quaternion:
        p = qt.quaternion(0)
        p.vec = omega - self.bhat + self.kp*w_mes


        # Q dot:
        qhatdot = 1/2. * qprod(self._qhat, p)

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
    ahrs = Ahrs()
    df = pd.read_hdf('data/N=500_d54d371192.hdf5')

    bias = df.loc[:10, ['wx', 'wy', 'wz']].values.mean(axis=0)/180*np.pi

    N = 600
    acc_arr = df.loc[:, ['ax', 'ay', 'az']].values[:N]
    omega_arr = df.loc[:, ['wx', 'wy', 'wz']].values[:N]
    times = np.cumsum(df.loc[:, 'dt'].values[:N])

    mahony = Mahony(bias=bias)
    mahony2 = Mahony2()
    madgwick = Madgwick()

    mah = np.empty((len(times), 3))
    mad_arr = mah.copy()
    mah2_arr = mah.copy()
    aharr = mah.copy()
    i = 0
    mah2_prev = np.array([1.,0,0,0])
    madgwick_prev = np.array([1.,0,0,0])
    for acc, omega in zip(acc_arr, omega_arr):

        dt = df.loc[i, 'dt']

        #acc = np.array([0,.01,1.])
        #omega = np.array([0,0.,0])

        q1 = qt.from_euler_angles(ahrs.quaternion.to_euler())

        q = mahony.qhat
        #print(q1*q1.conjugate(), q*q.conjugate())

        ahrs.update_no_magnetometer(omega, acc, dt)
        acc /= np.sqrt((acc**2).sum())
        omega = omega/180*np.pi

        mahony.update(acc, omega, dt)

        mahony2.Dt = dt #100 #new_sample_rate
        mah2_prev = mahony2.updateIMU(mah2_prev, gyr=omega, acc=acc)


        madgwick.Dt = dt
        madgwick_prev = madgwick.updateIMU(madgwick_prev, gyr=omega, acc=acc)



        mah[i] = q2eul(mahony.qhat)/np.pi*180
        aharr[i] = ahrs.quaternion.to_euler()
        mah2_arr[i] = q2eul(qt.quaternion(*mah2_prev))/np.pi*180
        mad_arr[i] = q2eul(qt.quaternion(*madgwick_prev))/np.pi*180

        R = qt.as_rotation_matrix(qt.quaternion(*mah2_prev)) #, mahony.qhat)
        ahrs_q = qt.from_euler_angles(aharr[i]/180*np.pi)
        ahrs_euler_inv = qt.as_euler_angles(ahrs_q)

        print('LOOK AT ME!')
        print(ahrs.quaternion.to_euler() - ahrs_euler_inv)
        print('ABOVE should be 0, 0, 0')
        R2 = qt.as_rotation_matrix(ahrs_q)

        print(mah2_prev)
        print(ahrs_q)
        print(qt.from_rotation_matrix(R2))

        for col, col2, lab in zip(R.T, R2.T, ('x', 'y', 'z')):
            print(f'{lab}-->{col} / {col2}') #, np.linalg.norm(col)):w


        mah_q = mahony.qhat
        mah2_q = qt.quaternion(*mah2_prev)

        #print(mah2_q)
        #mah[i] = (mah_q.conjugate()*qt.quaternion(0,0,0,-1)*mah_q).vec
        q = mah_q
        print((q.conjugate()*qt.quaternion(0,1,0,0)*q).vec)
        print((q.conjugate()*qt.quaternion(0,0,1,0)*q).vec)
        print((q.conjugate()*qt.quaternion(0,0,0,1)*q).vec)
        print()
        i += 1



    _, (ax1, ax2, ax3, ax4) = plt.subplots(4,1, sharex=True)
    for i, lab in zip(range(3), ('pitch', 'roll', 'yaw')):
        ax1.plot(times, mah2_arr[:, i], label=lab)
        ax2.plot(times, mah[:, i], label=lab)
        ax3.plot(times, aharr[:, i], label=lab)
        ax4.plot(times, mad_arr[:, i], label=lab)

    ax3.set_title('TRUE')
    print(qt.from_euler_angles(0,0,0))
    ax1.legend()
    plt.show()

