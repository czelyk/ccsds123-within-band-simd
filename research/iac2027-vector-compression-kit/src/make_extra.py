"""Regenerate the supplied band-count and larger-image reference fixtures."""
from pathlib import Path
import numpy as np
from scipy.io import loadmat
import make_frame as model

kit = Path(__file__).resolve().parent.parent
image = loadmat(model.DATA / 'PaviaU.mat')['paviaU'].astype(np.int64)
model.HERE = kit / 'band_matrix'
model.HERE.mkdir(exist_ok=True)
for bands in (1, 2, 3, 4, 8):
    model.generate(image[:64, :128, :bands], f'pavia_b{bands}', 9)
model.HERE = kit / 'large'
model.HERE.mkdir(exist_ok=True)
model.generate(image[:256, :256, :8], 'pavia256x256x8', 9)
