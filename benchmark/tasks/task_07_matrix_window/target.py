"""二维网格局部窗口均值与能量超标区域检测模块。"""

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
    """计算以 (top, left) 为左上角、尺寸为 (win_h, win_w) 的子窗口均值与总体方差。"""
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
    """扫描全部合法窗口位置，返回满足 mean >= min_mean 且 std >= min_std 的窗口列表。"""
    rows, cols = validate_grid(grid)
    if win_h <= 0 or win_w <= 0 or win_h > rows or win_w > cols:
        return []
    min_var = min_std * min_std
    anomalies: list[tuple[int, int, float, float]] = []
    for r in range(rows - win_h + 1):
        for c in range(cols - win_w + 1):
            mean, var = window_mean_and_variance(grid, r, c, win_h, win_w)
            if mean >= min_mean and var >= min_var:
                anomalies.append((r, c, round(mean, 6), round(var ** 0.5, 6)))
    return anomalies
