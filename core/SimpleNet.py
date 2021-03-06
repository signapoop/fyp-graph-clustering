import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from util.training_utils import get_torch_dtype


dtypeFloat, dtypeLong = get_torch_dtype()


class SimpleNet(nn.Module):
    """
    Implements a simple feed-forward net
    """

    def __init__(self, net_parameters):
        super(SimpleNet, self).__init__()

        self.name = 'simple_net'

        n_units_1 = 500
        n_units_2 = 500
        n_units_3 = 2000
        #n_units_4 = 500
        input_size = net_parameters['D']
        n_components = net_parameters['n_components']

        self.fc1 = nn.Linear(input_size, n_units_1)
        self.fc2 = nn.Linear(n_units_1, n_units_2)
        self.fc3 = nn.Linear(n_units_2, n_units_3)
        self.relu = nn.ReLU()
        self.fc4 = nn.Linear(n_units_3, n_components)

    def forward(self, G):
        # Data matrix
        x = G.inputs

        # Unroll into single vector
        x = x.view(x.shape[0], -1)

        # Pass raw data matrix X directly as input
        x = Variable(torch.FloatTensor(x).type(dtypeFloat), requires_grad=False)

        out = F.relu(self.fc1(x))
        out = F.relu(self.fc2(out))
        out = self.fc3(out)
        out = self.relu(out)
        out = self.fc4(out)
        return out

    def loss(self, y, y_target):
        # L2 loss
        loss = nn.MSELoss()(y, y_target)

        return loss

    def pairwise_loss(self, y, y_target, W):
        distances_1 = y_target[W.row, :] - y_target[W.col, :]
        distances_2 = y[W.row, :] - y[W.col, :]
        loss = torch.mean(torch.pow(distances_1.norm(dim=1) - distances_2.norm(dim=1), 2))

        return loss

    def update(self, lr):
        update = torch.optim.Adam(self.parameters(), lr=lr)

        return update

    def update_learning_rate(self, optimizer, lr):
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr

        return optimizer

    def nb_param(self):
        return self.nb_param
