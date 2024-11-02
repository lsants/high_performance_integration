import torch
from .mlp import MLP

class VanillaDeepONet(torch.nn.Module):
    def __init__(self, branch_layers, trunk_layers, activation):
        super().__init__()
        self.branch_network = MLP(branch_layers, activation)
        self.trunk_network = MLP(trunk_layers, activation)

    def forward(self, xb, xt):
        branch_out = self.branch_network(xb)
        trunk_out = self.trunk_network(xt)
        num_basis = trunk_out.shape[1]
        branch_real_out = branch_out[ : , : num_basis]
        branch_imag_out = branch_out[ : , num_basis : ]

        real_out = torch.matmul(branch_real_out, torch.transpose(trunk_out, 0, 1))
        imag_out = torch.matmul(branch_imag_out, torch.transpose(trunk_out, 0, 1))

        return real_out, imag_out