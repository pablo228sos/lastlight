"""Small GRU residual over the previous-week seasonal prediction."""

import torch
from torch import nn


class EnergyDNA(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(input_size=2, hidden_size=16, batch_first=True)
        self.head = nn.Sequential(nn.Linear(24, 16), nn.ReLU(), nn.Linear(16, 1))
        nn.init.zeros_(self.head[-1].weight)
        nn.init.zeros_(self.head[-1].bias)

    def forward(self, sequence, static):
        _, state = self.gru(sequence)
        residual = self.head(torch.cat((state[-1], static), dim=1)).squeeze(1)
        return (static[:, 2] + residual).clamp_min(0)
