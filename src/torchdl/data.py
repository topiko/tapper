
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from torch.utils.data import Dataset

plt.style.use('pltstyle.mplstyle')

class TapperDataset(Dataset):
    def __init__(self,data_file : str,
                 ntimesteps : int = 40,
                 stride : int = 5):

        if data_file.endswith('*'):
            data_files = []
            if '/' in data_file:
                pdir = '/'.join(data_file.split('/')[:-1])
            else:
                pdir = '.'
            fname = data_file.split('/')[-1][:-1]
            for f in os.listdir(pdir):
                if f.startswith(fname):
                    data_files.append(pdir + '/' + f)

            df = pd.concat([pd.read_hdf(fn) for fn in data_files], axis=0)
            self.df = df.reset_index(drop=True)
        else:
            self.df = pd.read_hdf(data_file)

        self.stride = stride
        self.ntimesteps = ntimesteps
        self.data = self.df.loc[:, ['ax', 'ay', 'az',
                                    'wx', 'wy', 'wz']].values.astype(np.float32)

        self.labels = self.df.sw.values

    def __len__(self):
        return (len(self.data) - self.ntimesteps)//self.stride

    def __getitem__(self, idx):
        start = idx*self.stride
        data = self.data[start : start + self.ntimesteps].T
        label = self.labels[start : start + self.ntimesteps]
        label = any(np.diff(label) == 1)
        if label:
            label = np.array([0,1.])
        else:
            label = np.array([1,0.])

        data = data[np.newaxis, :]

        return data, label

def plot_one_sample(X, y):
    X = X.T
    _, (ax1, ax2) = plt.subplots(2,1, sharex=True)
    for ax, dat in zip((ax1, ax2), (X[:, :3], X[:, 3:])):
        for i in range(3):
            ax.plot(range(len(dat)), dat[:,i])
    ax1.set_title(y)
    plt.show()


