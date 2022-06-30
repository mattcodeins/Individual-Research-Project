import torch
import torch.nn as nn
# import numpy as np
# import matplotlib.pyplot as plt
# import torchvision

from modules.bnn.modules.ext_emp_linear import make_linear_ext_emp_bnn
from modules.bnn.modules.loss import GaussianKLLoss, nELBO
from modules.utils import *

import datasets.mnist as d


torch.manual_seed(1)
experiment_name = 'mnist_emp_bnn_multiprior'

# create dataset
batch_size_train = 64
batch_size_test = 1000
train_loader, test_loader = d.import_n_mnist(batch_size_train, batch_size_test)

# create bnn
device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
x_dim, y_dim = 784, 10
h1_dim, h2_dim = 128, 64
layer_sizes = [x_dim, h1_dim, h2_dim, y_dim]
activation = nn.GELU()
model = make_linear_ext_emp_bnn(layer_sizes, activation=activation, device=device)
print("BNN architecture: \n", model)

# training hyperparameters
learning_rate = 1e-4
params = list(model.parameters())
opt = torch.optim.Adam(params, lr=learning_rate)
N_epochs = 2000

# define loss function (-ELBO)
cross_entropy_loss = nn.CrossEntropyLoss(reduction='sum')
kl_loss = GaussianKLLoss()
nelbo = nELBO(nll_loss=cross_entropy_loss, kl_loss=kl_loss)

train_logs = training_loop(model, N_epochs, opt, nelbo, train_loader, test_loader, experiment_name)

plot_training_loss(train_logs)
write_logs_to_file(train_logs, experiment_name)
