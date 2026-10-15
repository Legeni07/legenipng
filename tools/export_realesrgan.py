"""Exporte Real-ESRGAN « general x4v3 » en ONNX, à trois niveaux de débruitage.

Exécuté une seule fois, dans l'étape de construction jetable de l'image Docker :
PyTorch n'est pas embarqué dans l'image finale, seul ONNX Runtime l'est.

Le niveau de débruitage est obtenu comme dans Real-ESRGAN (« deep network
interpolation ») : poids = d * x4v3 + (1 - d) * wdn-x4v3, où x4v3 débruite
fortement et wdn-x4v3 conserve le grain.
"""
import argparse
import os

import onnx
import torch
from torch import nn
from torch.nn import functional as F


class SRVGGNetCompact(nn.Module):
    """Architecture compacte de Real-ESRGAN (identique à basicsr.archs.srvgg_arch)."""

    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList()
        self.body.append(nn.Conv2d(num_in_ch, num_feat, 3, 1, 1))
        self.body.append(nn.PReLU(num_parameters=num_feat))
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for layer in self.body:
            out = layer(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")


def load_state(path):
    state = torch.load(path, map_location="cpu", weights_only=True)
    for key in ("params_ema", "params"):
        if key in state:
            return state[key]
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strong", required=True, help="realesr-general-x4v3.pth")
    ap.add_argument("--weak", required=True, help="realesr-general-wdn-x4v3.pth")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    strong, weak = load_state(args.strong), load_state(args.weak)
    assert strong.keys() == weak.keys(), "les deux modèles n'ont pas la même architecture"

    for pct in (0, 50, 100):
        d = pct / 100.0
        mixed = {k: d * strong[k] + (1 - d) * weak[k] for k in strong}
        model = SRVGGNetCompact()
        model.load_state_dict(mixed, strict=True)
        model.eval()
        path = os.path.join(args.out, f"realesr-general-x4v3_dn{pct}.onnx")
        dummy = torch.rand(1, 3, 64, 64)
        with torch.no_grad():
            expected = model(dummy)
            torch.onnx.export(
                model,
                dummy,
                path,
                input_names=["input"],
                output_names=["output"],
                dynamic_axes={"input": {0: "n", 2: "h", 3: "w"}, "output": {0: "n", 2: "h4", 3: "w4"}},
                opset_version=17,
            )
        onnx.checker.check_model(onnx.load(path))
        assert tuple(expected.shape) == (1, 3, 256, 256)
        print(f"{path} : {os.path.getsize(path) / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
