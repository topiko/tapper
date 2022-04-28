import torch
import matplotlib.pyplot as plt

from torch.utils.data import DataLoader
from torchdl.models import ForwardModel
from torchdl.models import ConvModel
from torchdl.data import TapperDataset

from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report

TRAINDIR = 'data/train/N*'
TESTDIR = 'data/test/N*'
NTIMESTEPS = 30
NEPOCHS = 10

def train_one_epoch():
    size = len(train_dataloader.dataset)
    for i, (X,y) in enumerate(train_dataloader):
        pred = model(X)
        loss = loss_fn(pred, y)

        # Optim
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if i%100 == 0:
            loss, current = loss.item(), i*len(X)
            print(f'\tLoss = {loss:>7f}, [{current:>6d}/{size}]')


def eval_on_valid(plot_ = False):

    t_loss = 0
    all_preds = []
    all_ys = []
    with torch.no_grad():
        for i, (X,y) in enumerate(test_dataloader):
            preds = model(X)
            all_preds.append(preds)
            all_ys.append(y)
            t_loss += loss_fn(preds, y).item()

    preds = torch.concat(all_preds).argmax(1).numpy()
    ys = torch.concat(all_ys).argmax(1).numpy()

    labs = ['notap', 'tap']
    print(t_loss/len(test_dataloader))
    print(classification_report(ys, preds,
                                target_names=labs,
                                digits=3))
    if plot_:
        conf_mat = confusion_matrix(ys, preds, normalize=None)

        """C : ndarray of shape (n_classes, n_classes)
            Confusion matrix whose i-th row and j-th
            column entry indicates the number of
            samples with true label being i-th class
            and predicted label being j-th class."""

        plt.figure(figsize=(6,5))
        cm = plt.imshow(conf_mat, cmap='binary')
        for i, row in enumerate(conf_mat):
            for j, col in enumerate(row):
                print(i,j, col)
                plt.text(j, i, conf_mat[i,j],
                         fontdict={'fontsize':20, 'color':'blue'},
                         va='center', ha='center')

        plt.ylabel('True')
        plt.xlabel('Pred')
        plt.colorbar(cm)
        plt.xticks([0,1], labs)
        plt.yticks([0,1], labs)
        plt.show()

if __name__ == '__main__':

    #model = ForwardModel(ntimesteps=NTIMESTEPS)
    model = ConvModel(ntimesteps=NTIMESTEPS)

    print(model)



    train_ds = TapperDataset(TRAINDIR,
                             ntimesteps=NTIMESTEPS)

    train_dataloader = DataLoader(train_ds,
                                  batch_size=12,
                                  shuffle=False)
    test_ds = TapperDataset(TESTDIR,
                             ntimesteps=NTIMESTEPS)

    test_dataloader = DataLoader(test_ds,
                                 batch_size=10,
                                 shuffle=False)




    loss_fn = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=.001)

    for epoch in range(NEPOCHS+1):
        print(f'Epoch : {epoch}')
        train_one_epoch()
        if epoch%10==0:
            eval_on_valid(epoch==NEPOCHS)

