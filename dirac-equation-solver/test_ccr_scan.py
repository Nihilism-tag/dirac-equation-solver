"""
Unit tests for ccr_scan.py with stubbed solver.

Tests validate:
- Grid generation (endpoints, step size)
- Expected eigenvalue count formula
- Scan output shapes and NaN handling
- Exception handling during scan
- NPZ round-trip (save/load)

All tests use small N (10) and stub solver to avoid heavy compute.
"""

import tempfile
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest

try:
    from . import ccr_scan
except ImportError:
    # Fallback for when run as a script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import ccr_scan  # pyright: ignore[reportImplicitRelativeImport]


# ============================================================================
# Fixtures: Stub Solver
# ============================================================================


def stub_solver_basic(
    N: int,
    L: float,
    alpha_map: float,
    Z: int,
    lambda_shield: float,
    kappa: int,
    c: float,
    theta: float,
    return_complex: bool = True,
) -> tuple[npt.NDArray[np.complex128], None, None]:
    """
    Stub solver returning deterministic eigenvalues.
    Returns (E_complex, None, None) where E_complex has shape (2*(N-2),).
    """
    n_eig = 2 * (N - 2)
    # Deterministic: eigenvalues = 1 + 2j, 2 + 3j, ..., n_eig + (n_eig+1)j
    E_complex = np.array(
        [float(k) + 1j * float(k + 1) for k in range(1, n_eig + 1)],
        dtype=np.complex128,
    )
    return E_complex, None, None


def stub_solver_with_nan(
    N: int,
    L: float,
    alpha_map: float,
    Z: int,
    lambda_shield: float,
    kappa: int,
    c: float,
    theta: float,
    return_complex: bool = True,
) -> tuple[npt.NDArray[np.complex128], None, None]:
    """
    Stub solver that returns NaN/Inf in some eigenvalues.
    """
    n_eig = 2 * (N - 2)
    E_complex = np.array(
        [float(k) + 1j * float(k + 1) for k in range(1, n_eig + 1)],
        dtype=np.complex128,
    )
    # Inject NaN in first eigenvalue
    E_complex[0] = np.nan + 1j * np.nan
    return E_complex, None, None


def stub_solver_exception(
    N: int,
    L: float,
    alpha_map: float,
    Z: int,
    lambda_shield: float,
    kappa: int,
    c: float,
    theta: float,
    return_complex: bool = True,
) -> tuple[npt.NDArray[np.complex128], None, None]:
    """
    Stub solver that raises an exception.
    """
    raise RuntimeError("Stub solver intentional failure")


# ============================================================================
# Tests: make_theta_grid
# ============================================================================


class TestMakeThetaGrid:
    """Test grid generation with various step sizes and ranges."""

    def test_single_point(self):
        """Grid with zero range should return single point."""
        thetas = ccr_scan.make_theta_grid(0.0, 0.0, 0.1)
        assert thetas.shape == (1,)
        assert np.isclose(thetas[0], 0.0)

    def test_two_points(self):
        """Grid with step equal to range should return two points."""
        thetas = ccr_scan.make_theta_grid(0.0, 1.0, 1.0)
        assert thetas.shape == (2,)
        assert np.isclose(thetas[0], 0.0)
        assert np.isclose(thetas[1], 1.0)

    def test_multiple_points_includes_endpoints(self):
        """Grid should include both start and stop (within floating-point tolerance)."""
        thetas = ccr_scan.make_theta_grid(0.0, 1.0, 0.25)
        assert thetas.shape == (5,)
        assert np.isclose(thetas[0], 0.0)
        assert np.isclose(thetas[-1], 1.0)
        # Check step size
        diffs = np.diff(thetas)
        assert np.allclose(diffs, 0.25)

    def test_step_size_respected(self):
        """Grid spacing should match requested step."""
        thetas = ccr_scan.make_theta_grid(0.1, 0.5, 0.1)
        diffs = np.diff(thetas)
        assert np.allclose(diffs, 0.1)

    def test_invalid_step_raises(self):
        """Negative or zero step should raise ValueError."""
        with pytest.raises(ValueError, match="theta_step must be > 0"):
            ccr_scan.make_theta_grid(0.0, 1.0, 0.0)
        with pytest.raises(ValueError, match="theta_step must be > 0"):
            ccr_scan.make_theta_grid(0.0, 1.0, -0.1)

    def test_invalid_range_raises(self):
        """theta_stop < theta_start should raise ValueError."""
        with pytest.raises(ValueError, match="theta_stop must be >= theta_start"):
            ccr_scan.make_theta_grid(1.0, 0.0, 0.1)


# ============================================================================
# Tests: expected_eig_count
# ============================================================================


class TestExpectedEigCount:
    """Test eigenvalue count formula."""

    def test_formula_n_10(self):
        """For N=10, expected count is 2*(10-2)=16."""
        assert ccr_scan.expected_eig_count(10) == 16

    def test_formula_n_5(self):
        """For N=5, expected count is 2*(5-2)=6."""
        assert ccr_scan.expected_eig_count(5) == 6

    def test_formula_n_3(self):
        """For N=3, expected count is 2*(3-2)=2."""
        assert ccr_scan.expected_eig_count(3) == 2

    def test_formula_n_2(self):
        """For N=2, expected count is 2*(2-2)=0."""
        assert ccr_scan.expected_eig_count(2) == 0


# ============================================================================
# Tests: run_scan
# ============================================================================


class TestRunScan:
    """Test scan execution with stubbed solver."""

    def test_output_shape_basic(self, monkeypatch):
        """Output arrays should have shape (n_theta, n_eig_expected)."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_basic)

        N = 10
        thetas = ccr_scan.make_theta_grid(0.0, 0.2, 0.1)
        E_re, E_im = ccr_scan.run_scan(
            thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_basic
        )

        n_theta = len(thetas)
        n_eig = ccr_scan.expected_eig_count(N)
        assert E_re.shape == (n_theta, n_eig)
        assert E_im.shape == (n_theta, n_eig)

    def test_output_dtype_float64(self, monkeypatch):
        """Output arrays should be float64."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_basic)

        N = 10
        thetas = np.array([0.0, 0.1])
        E_re, E_im = ccr_scan.run_scan(
            thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_basic
        )

        assert E_re.dtype == np.float64
        assert E_im.dtype == np.float64

    def test_values_from_stub_solver(self, monkeypatch):
        """Values should match stub solver output (real and imaginary parts)."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_basic)

        N = 10
        thetas = np.array([0.0])
        E_re, E_im = ccr_scan.run_scan(
            thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_basic
        )

        # stub_solver_basic returns k + (k+1)j for k=1..n_eig
        n_eig = ccr_scan.expected_eig_count(N)
        expected_re = np.array([float(k) for k in range(1, n_eig + 1)])
        expected_im = np.array([float(k + 1) for k in range(1, n_eig + 1)])

        assert np.allclose(E_re[0, :], expected_re)
        assert np.allclose(E_im[0, :], expected_im)

    def test_nan_handling(self, monkeypatch, capsys):
        """NaN/Inf in solver output should be propagated to result."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_with_nan)

        N = 10
        thetas = np.array([0.0])
        E_re, E_im = ccr_scan.run_scan(
            thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_with_nan
        )

        # First eigenvalue should be NaN
        assert np.isnan(E_re[0, 0])
        assert np.isnan(E_im[0, 0])
        # Others should be finite
        assert np.all(np.isfinite(E_re[0, 1:]))
        assert np.all(np.isfinite(E_im[0, 1:]))

        # Check warning message
        captured = capsys.readouterr()
        assert "NaN/Inf" in captured.out

    def test_exception_handling(self, monkeypatch, capsys):
        """If solver raises exception, that row should remain all-NaN."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_exception)

        N = 10
        thetas = np.array([0.0, 0.1])
        E_re, E_im = ccr_scan.run_scan(
            thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_exception
        )

        # Both rows should be all-NaN due to exception
        assert np.all(np.isnan(E_re[0, :]))
        assert np.all(np.isnan(E_im[0, :]))
        assert np.all(np.isnan(E_re[1, :]))
        assert np.all(np.isnan(E_im[1, :]))

        # Check warning message
        captured = capsys.readouterr()
        assert "solver failed" in captured.out

    def test_multiple_thetas(self, monkeypatch):
        """Scan should process multiple theta values independently."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_basic)

        N = 10
        thetas = ccr_scan.make_theta_grid(0.0, 0.3, 0.1)
        E_re, E_im = ccr_scan.run_scan(
            thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_basic
        )

        # All rows should have same values (stub solver is deterministic)
        assert np.allclose(E_re[0, :], E_re[1, :])
        assert np.allclose(E_re[1, :], E_re[2, :])


# ============================================================================
# Tests: save_npz and round-trip
# ============================================================================


class TestSaveNpz:
    """Test NPZ save/load round-trip."""

    def test_save_creates_file(self):
        """save_npz should create a .npz file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = str(Path(tmpdir) / "test.npz")

            E_re = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
            E_im = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float64)
            thetas = np.array([0.0, 0.1], dtype=np.float64)
            metadata = {"N": 10, "L": 1.0}

            ccr_scan.save_npz(out_path, E_re, E_im, thetas, metadata)

            assert Path(out_path).exists()

    def test_round_trip_preserves_data(self):
        """Data should be preserved through save/load cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = str(Path(tmpdir) / "test.npz")

            E_re = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
            E_im = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float64)
            thetas = np.array([0.0, 0.1], dtype=np.float64)
            metadata = {"N": 10, "L": 1.0, "alpha": 0.5}

            ccr_scan.save_npz(out_path, E_re, E_im, thetas, metadata)

            # Load and verify
            data = np.load(out_path)
            assert np.allclose(data["E_re"], E_re)
            assert np.allclose(data["E_im"], E_im)
            assert np.allclose(data["thetas"], thetas)
            assert np.isclose(data["N"], 10.0)
            assert np.isclose(data["L"], 1.0)
            assert np.isclose(data["alpha"], 0.5)

    def test_round_trip_preserves_shapes(self):
        """Array shapes should be preserved through save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = str(Path(tmpdir) / "test.npz")

            E_re = np.random.randn(5, 16).astype(np.float64)
            E_im = np.random.randn(5, 16).astype(np.float64)
            thetas = np.linspace(0.0, 0.4, 5, dtype=np.float64)
            metadata: dict[str, float | int] = {"N": 10}

            ccr_scan.save_npz(out_path, E_re, E_im, thetas, metadata)

            data = np.load(out_path)
            assert data["E_re"].shape == (5, 16)
            assert data["E_im"].shape == (5, 16)
            assert data["thetas"].shape == (5,)

    def test_round_trip_preserves_dtype(self):
        """Data types should be float64 after round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = str(Path(tmpdir) / "test.npz")

            E_re = np.array([[1.0, 2.0]], dtype=np.float64)
            E_im = np.array([[0.1, 0.2]], dtype=np.float64)
            thetas = np.array([0.0], dtype=np.float64)
            metadata: dict[str, float | int] = {"N": 10}

            ccr_scan.save_npz(out_path, E_re, E_im, thetas, metadata)

            data = np.load(out_path)
            assert data["E_re"].dtype == np.float64
            assert data["E_im"].dtype == np.float64
            assert data["thetas"].dtype == np.float64


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_workflow(self, monkeypatch):
        """Full workflow: grid → scan → save → load."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_basic)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = str(Path(tmpdir) / "scan.npz")

            # Generate grid
            thetas = ccr_scan.make_theta_grid(0.0, 0.2, 0.1)
            N = 10

            # Run scan
            E_re, E_im = ccr_scan.run_scan(
                thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_basic
            )

            # Save
            metadata = {"N": N, "L": 1.0, "alpha": 0.5}
            ccr_scan.save_npz(out_path, E_re, E_im, thetas, metadata)

            # Load and verify
            data = np.load(out_path)
            assert data["E_re"].shape == (3, 16)
            assert data["E_im"].shape == (3, 16)
            assert data["thetas"].shape == (3,)
            assert np.isclose(data["N"], 10.0)

    def test_scan_with_nan_and_save(self, monkeypatch):
        """Scan with NaN values should save correctly."""
        monkeypatch.setattr(ccr_scan, "solve_mabgps_ccr", stub_solver_with_nan)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = str(Path(tmpdir) / "scan_nan.npz")

            thetas = np.array([0.0, 0.1])
            N = 10

            E_re, E_im = ccr_scan.run_scan(
                thetas, N=N, L=1.0, alpha_map=0.5, solver=stub_solver_with_nan
            )

            ccr_scan.save_npz(out_path, E_re, E_im, thetas, {"N": N})

            # Load and verify NaN is preserved
            data = np.load(out_path)
            assert np.isnan(data["E_re"][0, 0])
            assert np.isnan(data["E_im"][0, 0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
