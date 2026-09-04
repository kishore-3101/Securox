import random

import numpy as np

from src.config.paths import RANDOM_SEED


def set_global_seed(seed: int = RANDOM_SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
