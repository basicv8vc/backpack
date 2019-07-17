import torch.nn
from ...core.layers import Conv2dConcat
from ...utils.utils import einsum
from ...utils import conv as convUtils
from ...extensions import GRAD
from ..firstorder import FirstOrderExtension


class GradConv2d(FirstOrderExtension):
    def __init__(self):
        super().__init__(torch.nn.Conv2d, GRAD, params=["bias", "weight"])

    def bias(self, module, grad_input, grad_output):
        return grad_output[0].sum(3).sum(2).sum(0)

    def weight(self, module, grad_input, grad_output):
        X, dE_dY = convUtils.get_weight_gradient_factors(
            module.input0, grad_output[0], module)
        return einsum('bml,bkl->mk', (dE_dY, X)).view(module.weight.size())


class GradConv2dConcat(FirstOrderExtension):
    def __init__(self):
        super().__init__(Conv2dConcat, GRAD, params=["weight"])

    def weight(self, module, grad_input, grad_output):
        X, dE_dY = convUtils.get_weight_gradient_factors(
            module.input0, grad_output[0], module)

        if module.has_bias():
            X = module.append_ones(X)

        return einsum('bml,bkl->mk', (dE_dY, X)).view(module.weight.size())
