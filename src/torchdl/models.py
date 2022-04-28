import torch

NOUTPUTS = 2
NCHANNELS = 6

class ForwardModel(torch.nn.Module):

    def __init__(self, ntimesteps=20):
        super(ForwardModel, self).__init__()

        self.ntimesteps = ntimesteps
        self.flatten = torch.nn.Flatten()
        self.linear1 = torch.nn.Linear(ntimesteps*NCHANNELS, 200)
        self.activation1 = torch.nn.ReLU()
        self.linear2 = torch.nn.Linear(200, 200)
        self.activation2 = torch.nn.ReLU()
        self.linear3 = torch.nn.Linear(200, NOUTPUTS)
        self.softmax = torch.nn.Softmax(dim=1)

    def forward(self, x):

        x = self.flatten(x)
        x = self.linear1(x)
        x = self.activation1(x)
        x = self.linear2(x)
        x = self.activation2(x)
        x = self.linear3(x)
        x = self.softmax(x)
        return x

class ConvModel(torch.nn.Module):

    def __init__(self,
                 ntimesteps : int = 30):

        super(ConvModel, self).__init__()

        assert ntimesteps==30 # supports only this as of now...

        self.ntimesteps = ntimesteps
        self.conv1 = torch.nn.Conv2d(1, 16, kernel_size=(6, 5), padding=0)
        # output shape = (1, ntimesteps - 4, 16)
        self.maxpool1 = torch.nn.MaxPool2d((1, 2), stride=2)
        # output shape = (1, (ntimesteps - 4)/2, 16)
        self.conv2 = torch.nn.Conv2d(16, 32, kernel_size=(1, 5), padding=0)
        # output shape = (1, (ntimesteps - 4)/2 - 4, 32)
        self.maxpool2 = torch.nn.MaxPool2d((1,3), stride=2)
        # output shape = (1, ((ntimesteps - 4)/2 - 4)/2 * 32)
        self.lin1 = torch.nn.Linear(32*4, 50)
        self.relu1 = torch.nn.ReLU()
        self.lin2 = torch.nn.Linear(50, NOUTPUTS)

        self.softmax = torch.nn.Softmax(dim=1)

    def forward(self, x):

        x = self.conv1(x)
        x = self.maxpool1(x)
        x = self.conv2(x)
        x = self.maxpool2(x)
        # Cast the shape into flat...
        x = x.view(-1, self.num_flat_features(x))
        x = self.lin1(x)
        x = self.relu1(x)
        x = self.lin2(x)
        x = self.softmax(x)

        return x

    def num_flat_features(self, x):
        sizes = x.size()[1:]
        num_features = 1
        for s in sizes:
            num_features *= s
        return num_features

