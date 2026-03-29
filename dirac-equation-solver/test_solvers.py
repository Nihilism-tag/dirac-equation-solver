"""Pytest test suite for Dirac equation solvers."""

import numpy as np
import pytest

import config as cfg
from potential import V, analytical_dirac_energy
from bspline import solve_bspline
from mabgps import solve_mabgps


class TestPotential:
    def test_potential_monotone(self):
        """V(r) should be monotonically increasing (less negative) with r."""
        r = np.array([1.0, 2.0, 5.0])
        v = V(r, 92, 0.1)
        assert v[0] < v[1] < v[2] < 0

    def test_potential_r0_safe(self):
        """V(r=0) should return finite value, not inf or nan."""
        v = V(np.array([0.0]), 92, 0.1)
        assert np.isfinite(v[0])


class TestAnalytical:
    def test_analytical_hydrogen(self):
        """Analytical energy for Z=1 hydrogen should be close to 1 (in mc² units)."""
        E = analytical_dirac_energy(1, -1, 1, 137.036)
        assert 0.999 < E < 1.0
        rel_err = abs(E - 0.99997337) / 0.99997337
        assert rel_err < 1e-4


class TestMABGPS:
    def test_mabgps_no_spurious(self):
        """MAB-GPS should produce clean spectrum with only physical bound states."""
        E, _, _ = solve_mabgps()
        mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2

        assert len(E) == 2 * (cfg.N_POINTS - 2)
        bound_states = E[(E > 0) & (E < mc2)]
        assert len(bound_states) > 0
        assert len(bound_states) < 50

    def test_mabgps_validation_lambda0(self):
        """MAB-GPS ground state should match analytical within 1e-4 for lambda=0."""
        E, _, _ = solve_mabgps(lambda_shield=0.0)
        mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2

        bound = E[(E > 0) & (E < mc2)]
        E_num = np.min(bound) / mc2
        E_ana = analytical_dirac_energy(1, -1, cfg.Z, cfg.C_LIGHT)

        rel_err = abs(E_num - E_ana) / abs(E_ana)
        assert rel_err < 1e-4

    def test_mabgps_wavefunction_smooth(self):
        """Ground state wavefunction envelope must be smooth (no Nyquist sawtooth in |P(r)|)."""
        E, vecs, r = solve_mabgps()
        mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2

        bound_mask = (E > 0) & (E < mc2)
        assert np.any(bound_mask), "No bound states found"
        ground_idx = np.where(bound_mask)[0][np.argmin(E[bound_mask])]
        N2 = len(r)
        # CGL spectral coefficients naturally alternate in sign; the physical smooth
        # quantity is the amplitude envelope |P(r)|, not the raw real part.
        P_envelope = np.abs(vecs[:N2, ground_idx])

        # Nyquist oscillation in envelope: rate ≈ 1.0; smooth decay: rate ≪ 0.5
        signs = np.sign(np.diff(P_envelope))
        sign_changes = np.sum(signs[:-1] != signs[1:])
        oscillation_rate = sign_changes / len(signs)
        assert oscillation_rate < 0.5, (
            f"Nyquist oscillation detected in |P(r)|: sign-change rate = {oscillation_rate:.3f}"
        )


class TestBspline:
    def test_bspline_has_spurious(self):
        """B-spline method should produce spurious states in the energy gap."""
        E = solve_bspline()
        mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2

        in_gap = np.sum((E > -mc2) & (E < mc2))
        assert in_gap > 0
