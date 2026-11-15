"""task_07_matrix_window 性能负载驱动。"""

import random
from target import detect_anomalous_windows


def build_inputs(seed: int = 53) -> tuple[list[list[float]], int, int, float, float]:
    rng = random.Random(seed)
    rows, cols = 175, 185
    grid = [
        [round(rng.uniform(0.0, 100.0) + (18.0 if (r > 60 and c > 70) else 0.0), 3) for c in range(cols)]
        for r in range(rows)
    ]
    return grid, 16, 18, 56.0, 27.5


def run_workload(inputs: tuple[list[list[float]], int, int, float, float]) -> int:
    grid, win_h, win_w, min_mean, min_std = inputs
    found = detect_anomalous_windows(grid, win_h, win_w, min_mean, min_std)
    return len(found)
