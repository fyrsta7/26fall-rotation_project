import unittest
from target import detect_anomalous_windows, window_mean_and_variance


class TestMatrixWindow(unittest.TestCase):
    def test_rectangular_window_and_boundaries(self) -> None:
        grid = [
            [1.0, 2.0, 10.0, 12.0],
            [1.0, 3.0, 14.0, 16.0],
            [0.0, 1.0, 2.0, 2.0],
        ]
        m, v = window_mean_and_variance(grid, 0, 2, 2, 2)
        self.assertAlmostEqual(m, 13.0)
        self.assertAlmostEqual(v, 5.0)

        res = detect_anomalous_windows(grid, win_h=2, win_w=2, min_mean=7.0, min_std=2.0)
        self.assertEqual([item[:2] for item in res], [(0, 1), (0, 2), (1, 2)])

    def test_oversized_or_single_cell_window(self) -> None:
        grid = [[5.0, 5.0], [5.0, 5.0]]
        self.assertEqual(detect_anomalous_windows(grid, 3, 2, 1.0, 0.0), [])
        self.assertEqual(len(detect_anomalous_windows(grid, 1, 1, 5.0, 0.0)), 4)

    def test_ragged_grid_raises(self) -> None:
        with self.assertRaises(ValueError):
            detect_anomalous_windows([[1.0, 2.0], [1.0]], 1, 1, 0.0, 0.0)


if __name__ == "__main__":
    unittest.main()
