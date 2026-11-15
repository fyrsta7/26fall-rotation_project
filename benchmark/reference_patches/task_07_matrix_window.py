"""task_07_matrix_window 参考优化实现：构建二维前缀和与平方前缀和（积分图），将单窗口查询降至 O(1)。"""

from __future__ import annotations


def validate_grid(grid: list[list[float]]) -> tuple[int, int]:
    if not grid or not grid[0]:
        raise ValueError("Grid must be non-empty")
    rows = len(grid)
    cols = len(grid[0])
    for row in grid:
        if len(row) != cols:
            raise ValueError("Ragged grid is not supported")
    return rows, cols


def window_mean_and_variance(
    grid: list[list[float]],
    top: int,
    left: int,
    win_h: int,
    win_w: int,
) -> tuple[float, float]:
    total = 0.0
    total_sq = 0.0
    count = win_h * win_w
    for r in range(top, top + win_h):
        row = grid[r]
        for c in range(left, left + win_w):
            val = row[c]
            total += val
            total_sq += val * val
    mean = total / count
    variance = max(0.0, (total_sq / count) - (mean * mean))
    return mean, variance


def detect_anomalous_windows(
    grid: list[list[float]],
    win_h: int,
    win_w: int,
    min_mean: float,
    min_std: float,
) -> list[tuple[int, int, float, float]]:
    rows, cols = validate_grid(grid)
    if win_h <= 0 or win_w <= 0 or win_h > rows or win_w > cols:
        return []

    ps = [[0.0] * (cols + 1) for _ in range(rows + 1)]
    ps2 = [[0.0] * (cols + 1) for _ in range(rows + 1)]
    for r in range(rows):
        row = grid[r]
        ps_curr = ps[r + 1]
        ps_prev = ps[r]
        ps2_curr = ps2[r + 1]
        ps2_prev = ps2[r]
        row_sum = 0.0
        row_sq = 0.0
        for c in range(cols):
            v = row[c]
            row_sum += v
            row_sq += v * v
            ps_curr[c + 1] = ps_prev[c + 1] + row_sum
            ps2_curr[c + 1] = ps2_prev[c + 1] + row_sq

    inv_count = 1.0 / (win_h * win_w)
    min_var = min_std * min_std
    anomalies: list[tuple[int, int, float, float]] = []
    for r in range(rows - win_h + 1):
        r2 = r + win_h
        ps_top = ps[r]
        ps_bot = ps[r2]
        ps2_top = ps2[r]
        ps2_bot = ps2[r2]
        for c in range(cols - win_w + 1):
            c2 = c + win_w
            total = ps_bot[c2] - ps_top[c2] - ps_bot[c] + ps_top[c]
            mean = total * inv_count
            if mean < min_mean:
                continue
            total_sq = ps2_bot[c2] - ps2_top[c2] - ps2_bot[c] + ps2_top[c]
            var = max(0.0, total_sq * inv_count - mean * mean)
            if var >= min_var:
                anomalies.append((r, c, round(mean, 6), round(var ** 0.5, 6)))
    return anomalies
