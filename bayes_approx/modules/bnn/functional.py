import torch

from modules.bnn.modules.linear import BayesLinear
from modules.bnn.modules.emp_linear import EmpBayesLinear
from modules.bnn.modules.ext_emp_linear import ExtEmpBayesLinear
from modules.bnn.modules.marglikgrad_linear import MLGBayesLinear


def _gaussian_kl(mean_q, std_q, mean_p, std_p):
    """
    KL divergence between diagonal Gaussian distribtuions.
    (We can simply calculate the sum of the kl between independent single variate gaussians)
    """
    kl = (-0.5 + torch.log(std_p) - torch.log(std_q) +
          (torch.pow(std_q, 2) + torch.pow(mean_q-mean_p, 2)) /
          (2*torch.pow(std_p, 2)))
    return kl.sum()


def gaussian_kl_loss(model):
    """
    KL divergence between approximate posterior and prior, assuming both are diagonal Gaussian.
    This is the closed form complexity cost in Weight Uncertainty in Neural Networks.
    """
    device = torch.device("cuda" if next(model.parameters()).is_cuda else "cpu")
    kl = torch.Tensor([0]).to(device)
    kl_sum = torch.Tensor([0]).to(device)
    for m in model.modules():
        if (isinstance(m, (BayesLinear))
                or isinstance(m, (EmpBayesLinear))
                or isinstance(m, (ExtEmpBayesLinear))
                or isinstance(m, (MLGBayesLinear))):
            kl = _gaussian_kl(m.weight_mean, m.weight_std, m.prior_weight_mean, m.prior_weight_std)
            kl_sum += kl
            if m.bias:
                kl = _gaussian_kl(m.bias_mean, m.bias_std, m.prior_bias_mean, m.prior_bias_std)
                kl_sum += kl
    return kl_sum


def nelbo(model, loss_args, minibatch_ratio, nll_loss, kl_loss):
    """
    kl divided by number of minibatches
    """
    device = torch.device("cuda" if next(model.parameters()).is_cuda else "cpu")
    nelbo = torch.Tensor([0]).to(device)
    nll = nll_loss(*loss_args)
    kl = kl_loss(model) * minibatch_ratio
    nelbo = nll + kl

    return nelbo, nll, kl


def prior_regularisation(model):
    device = torch.device("cuda" if next(model.parameters()).is_cuda else "cpu")
    prior_dif = torch.Tensor([0]).to(device)
    prior_dif_sum = torch.Tensor([0]).to(device)
    for m in model.modules():
        if (isinstance(m, (BayesLinear))
                or isinstance(m, (EmpBayesLinear))
                or isinstance(m, (ExtEmpBayesLinear))
                or isinstance(m, (MLGBayesLinear))):
            prior_dif = _gaussian_kl(m.weight_mean, m.weight_std, m.prior_weight_mean, m.prior_weight_std)
            prior_dif_sum += kl
            if m.bias:
                kl = _gaussian_kl(m.bias_mean, m.bias_std, m.prior_bias_mean, m.prior_bias_std)
                kl_sum += kl
    return kl_sum


def maximum_a_posteriori(model, loss_args, minibatch_ratio, nll_loss):
    device = torch.device("cuda" if next(model.parameters()).is_cuda else "cpu")
    map_loss = torch.Tensor([0]).to(device)
    nll = nll_loss(*loss_args)
    prior_loss = prior_regularisation(model)
    map_loss = nll + prior_loss

    return map_loss, nll, prior_loss


def MLG_gaussian_kl(model):
    """
    KL divergence is between the epsilon posterior and prior (standard normal)
    """
    device = torch.device("cuda" if next(model.parameters()).is_cuda else "cpu")
    kl = torch.Tensor([0]).to(device)
    kl_sum = torch.Tensor([0]).to(device)
    for m in model.modules():   
        if isinstance(m, (MLGBayesLinear)):
            kl = _gaussian_kl(m.weight_mean, m.weight_std, torch.tensor(0), torch.tensor(1))
            kl_sum += kl
            if m.bias:
                kl = _gaussian_kl(m.bias_mean, m.bias_std, torch.tensor(0), torch.tensor(1))
                kl_sum += kl
    return kl_sum


def MLG_approximate_scheme(model, loss_args, minibatch_ratio, nll_loss, kl_loss):
    device = torch.device("cuda" if next(model.parameters()).is_cuda else "cpu")
    nelbo = torch.Tensor([0]).to(device)
    nll = nll_loss(*loss_args)
    kl = kl_loss(model) * minibatch_ratio
    nelbo = nll + kl

    return nelbo, nll, kl
