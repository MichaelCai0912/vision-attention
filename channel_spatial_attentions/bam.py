# Bam: Bottleneck attention module(BMVC 2018)
import torch
from torch import nn
from torch.nn import functional as F


class ChannelGate(nn.Module):
    def __init__(self, gate_channel, reduction_ratio=16, num_layers=1):
        super(ChannelGate, self).__init__()
        gate_c = []
        gate_c.append(nn.Flatten())
        gate_channels = [gate_channel]
        gate_channels += [gate_channel // reduction_ratio] * num_layers
        gate_channels += [gate_channel]
        for i in range(len(gate_channels) - 2):
            gate_c.append(nn.Linear(
                gate_channels[i], gate_channels[i+1]))
            gate_c.append(nn.BatchNorm1d(gate_channels[i+1]))
            gate_c.append(nn.ReLU())
        gate_c.append(nn.Linear(
            gate_channels[-2], gate_channels[-1]))
        self.gate_c = nn.Sequential(*gate_c)

    def forward(self, x):
        avg_pool = F.avg_pool2d(
            x, x.size(2), stride=x.size(2))
        return self.gate_c(avg_pool).unsqueeze(2).unsqueeze(3).expand_as(x)


class SpatialGate(nn.Module):
    def __init__(self, gate_channel, reduction_ratio=16, dilation_conv_num=2, dilation_val=4):
        super(SpatialGate, self).__init__()
        self.gate_s = []
        self.gate_s.append(nn.Conv2d(
            gate_channel, gate_channel//reduction_ratio, kernel_size=1))
        self.gate_s.append(nn.BatchNorm2d(
            gate_channel//reduction_ratio))
        self.gate_s.append(nn.ReLU())
        for i in range(dilation_conv_num):
            self.gate_s.append(nn.Conv2d(gate_channel//reduction_ratio, gate_channel//reduction_ratio, kernel_size=3,
                                         padding=dilation_val, dilation=dilation_val))
            self.gate_s.append(nn.BatchNorm2d(
                gate_channel//reduction_ratio))
            self.gate_s.append(nn.ReLU())
        self.gate_s.append(nn.Conv2d(
            gate_channel//reduction_ratio, 1, kernel_size=1))
        self.gate_s = nn.Sequential(*self.gate_s)

    def forward(self, x):
        return self.gate_s(x).expand_as(x)


class BAM(nn.Module):
    def __init__(self, gate_channel):
        super(BAM, self).__init__()
        self.channel_att = ChannelGate(gate_channel)
        self.spatial_att = SpatialGate(gate_channel)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        att = 1 + self.sigmoid(self.channel_att(x) * self.spatial_att(x))
        return att * x


def main():
    attention_block = BAM(64)
    input = torch.rand([4, 64, 32, 32])
    output = attention_block(input)
    print(input.size(), output.size())


if __name__ == '__main__':
    main()