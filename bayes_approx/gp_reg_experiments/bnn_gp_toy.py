import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from datasets.gp_reg_dataset import gp_regression as d
from modules.bnn.modules.linear import make_linear_bnn
from modules.bnn.modules.loss import GaussianKLLoss, nELBO
from modules.bnn.utils import *


torch.manual_seed(1)
experiment_name = 'bnn_gp_reg_19_06'

# import dataset
train_loader, test_loader, train, test, noise_std = d.create_regression_dataset()

# create bnn
device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
x_dim, y_dim = 1, 1
h_dim = 50
layer_sizes = [x_dim, h_dim, h_dim, y_dim]
activation = nn.ReLU()
layer_kwargs = {'prior_weight_std': 1.0,
                'prior_bias_std': 1.0,
                'sqrt_width_scaling': False,
                'init_std': 0.05,
                'device': device}
model = make_linear_bnn(layer_sizes, activation=activation, **layer_kwargs)
log_noise_var = nn.Parameter(torch.ones(size=(), device=device)*-3.0)  # Gaussian likelihood
print("BNN architecture: \n", model)

d.plot_bnn_pred_post(model, predict, train, test, log_noise_var, noise_std,
                     'BNN init (before training, MFVI)', device)

# training hyperparameters
learning_rate = 1e-4
params = list(model.parameters()) + [log_noise_var]
opt = torch.optim.Adam(params, lr=learning_rate)
N_epochs = 50000

gnll_loss = nn.GaussianNLLLoss(full=True, reduction='sum')
kl_loss = GaussianKLLoss()
nelbo = nELBO(nll_loss=gnll_loss, kl_loss=kl_loss)

logs = training_loop(model, N_epochs, opt, nelbo, train_loader, test_loader, log_noise_var, experiment_name, device)
plot_training_loss(logs)

d.plot_bnn_pred_post(model, predict, train, test, log_noise_var, noise_std,
                     'BNN approx. posterior (MFVI)', device)
