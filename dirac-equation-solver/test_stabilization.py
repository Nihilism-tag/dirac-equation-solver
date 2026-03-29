"""Pytest test suite for the stabilization method modules."""

import os

import numpy as np
import pytest

from stab_scan import scan_stabilization, track_levels, find_resonance


class TestScanStabilization:
    def test_scan_returns_correct_structure(self):
        """scan_stabilization returns dict with required keys and consistent lengths."""
        result = scan_stabilization(L_min=1.0, L_max=1.2, L_step=0.1, N=50)
        assert "L_arr" in result and "eigenvalue_sets" in result and "mc2" in result
        assert len(result["L_arr"]) == 3
        assert len(result["eigenvalue_sets"]) == 3
        assert result["mc2"] > 0

    def test_scan_eigenvalues_finite(self):
        """All returned eigenvalues must be finite (no NaN/inf)."""
        result = scan_stabilization(L_min=1.0, L_max=1.1, L_step=0.1, N=50)
        for eigs in result["eigenvalue_sets"]:
            assert np.all(np.isfinite(eigs))

    def test_scan_empty_window(self):
        """Scan with impossibly high energy window returns empty lists."""
        result = scan_stabilization(
            L_min=1.0,
            L_max=1.1,
            L_step=0.1,
            N=50,
            E_min_frac=99.0,
            E_max_frac=100.0,
        )
        assert all(len(e) == 0 for e in result["eigenvalue_sets"])


class TestTrackLevels:
    def test_perfect_plateau(self):
        """Track 2 levels: one rising, one flat. Trajectories correctly separated."""
        mc2 = 137.036**2
        L_arr = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
        eig_sets = [np.sort([1.05 * mc2, 1.0 * mc2 + i * 0.01 * mc2]) for i in range(5)]
        result = {"L_arr": L_arr, "eigenvalue_sets": eig_sets, "mc2": mc2}
        traj = track_levels(result)
        assert traj.shape[0] == 5
        assert traj.shape[1] >= 2

    def test_handles_empty_window(self):
        """track_levels handles all-empty eigenvalue_sets without crash."""
        mc2 = 137.036**2
        result = {
            "L_arr": np.array([1.0, 1.1, 1.2]),
            "eigenvalue_sets": [[], [], []],
            "mc2": mc2,
        }
        traj = track_levels(result)
        assert traj.shape[0] == 3


class TestFindResonance:
    def test_detects_flat_trajectory(self):
        """find_resonance returns the flat trajectory from synthetic data."""
        mc2 = 137.036**2
        L_arr = np.linspace(0.5, 3.0, 26)
        traj = np.column_stack(
            [
                np.full(26, 1.05 * mc2),
                1.0 * mc2 + 0.02 * mc2 * np.arange(26),
            ]
        )
        E_res, L_opt, res_idx = find_resonance(L_arr, traj, mc2)
        assert E_res is not None
        assert res_idx == 0
        assert abs(E_res / mc2 - 1.05) < 0.02

    def test_returns_none_for_empty_trajectories(self):
        """find_resonance returns (None, None, None) when no tracks pass coverage filter."""
        mc2 = 137.036**2
        L_arr = np.linspace(0.5, 3.0, 26)
        traj = np.full((26, 3), np.nan)
        result = find_resonance(L_arr, traj, mc2)
        assert result == (None, None, None)


class TestPlots:
    def test_plot_stabilization_headless(self, tmp_path):
        """plot_stabilization_graph runs under Agg backend without error."""
        import matplotlib

        matplotlib.use("Agg")
        from stab_plot import plot_stabilization_graph

        mc2 = 137.036**2
        L = np.linspace(0.5, 3.0, 10)
        traj = np.column_stack([mc2 * (1.05 - 0.001 * L), mc2 * (1.1 + 0.005 * L)])
        out = str(tmp_path / "test_stab.png")
        plot_stabilization_graph(L, traj, 0, mc2, save_path=out)
        assert os.path.getsize(out) > 5000

    def test_plot_resonance_wf_none_graceful(self, tmp_path):
        """plot_resonance_wavefunction handles None inputs gracefully."""
        import matplotlib

        matplotlib.use("Agg")
        from stab_plot import plot_resonance_wavefunction

        out = str(tmp_path / "test_wf.png")
        plot_resonance_wavefunction(None, None, save_path=out)
        assert os.path.exists(out)
