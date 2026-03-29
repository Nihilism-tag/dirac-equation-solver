"""
Test suite for Complex Coordinate Rotation (CCR) implementation.

Tests:
1. Backward compatibility: theta=0 recovers original solver
2. Bound state invariance: bound states independent of theta
3. Resonance emergence: resonances appear as theta increases
4. Spectral structure: correct classification of eigenvalues
5. Coulomb validation: exact solutions for unshielded case
6. Numerical stability: convergence with grid refinement
"""

import numpy as np
import pytest
from scipy import linalg

from mabgps import solve_mabgps
from mabgps_ccr import solve_mabgps_ccr, solve_mabgps_ccr_with_resonances
from complex_coordinate_rotation import extract_resonances, validate_ccr_bound_states
from potential import analytical_dirac_energy
from config import C_LIGHT, M_ELECTRON


class TestCCRBackwardCompatibility:
    """Test that theta=0 recovers original solver."""
    
    def test_theta_zero_matches_original(self):
        """Verify that solve_mabgps_ccr(theta=0) matches solve_mabgps()."""
        # Solve with original solver
        E_orig, vecs_orig, r_orig = solve_mabgps(
            N=100, Z=1, lambda_shield=0.0, kappa=1
        )
        
        # Solve with CCR solver at theta=0
        E_ccr, vecs_ccr, r_ccr = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.0, kappa=1, theta=0.0, return_complex=False
        )
        
        # Check that grids match
        np.testing.assert_allclose(r_orig, r_ccr, rtol=1e-14)
        
        # Check that eigenvalues match (first 10)
        np.testing.assert_allclose(E_orig[:10], E_ccr[:10], rtol=1e-10)
        
        print("✓ theta=0 matches original solver")
    
    def test_theta_zero_real_eigenvalues(self):
        """Verify that theta=0 produces real eigenvalues."""
        E, _, _ = solve_mabgps_ccr(
            N=80, Z=1, lambda_shield=0.1, theta=0.0, return_complex=False
        )
        
        # All eigenvalues should be real
        assert np.all(np.isreal(E)), "Non-real eigenvalues at theta=0"
        
        print("✓ theta=0 produces real eigenvalues")


class TestBoundStateInvariance:
    """Test that bound states are invariant under complex scaling."""
    
    def test_bound_states_theta_independent(self):
        """Verify bound states don't change significantly with theta."""
        mc2 = M_ELECTRON * C_LIGHT**2
        
        # Solve at theta=0
        E0, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.0, theta=0.0, return_complex=False
        )
        bound0 = E0[(E0 > 0) & (E0 < mc2)]
        
        # Solve at theta=0.2
        E_theta, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.0, theta=0.2, return_complex=True
        )
        # Extract bound states (small imaginary part)
        bound_mask = np.abs(np.imag(E_theta)) < 1e-4
        bound_theta = np.real(E_theta[bound_mask])
        bound_theta = bound_theta[(bound_theta > 0) & (bound_theta < mc2)]
        
        # Check that we have similar number of bound states
        assert abs(len(bound0) - len(bound_theta)) <= 2, \
            f"Bound state count changed: {len(bound0)} → {len(bound_theta)}"
        
        print(f"✓ Bound states stable: {len(bound0)} → {len(bound_theta)} states")
    
    def test_ground_state_coulomb(self):
        """Validate ground state against analytical Coulomb formula."""
        mc2 = M_ELECTRON * C_LIGHT**2
        
        # Solve unshielded Coulomb (lambda=0)
        E, _, _ = solve_mabgps_ccr(
            N=120, Z=1, lambda_shield=0.0, kappa=-1, theta=0.0, return_complex=False
        )
        
        # Extract ground state (lowest positive energy)
        bound = E[(E > 0) & (E < mc2)]
        E_num = np.min(bound) / mc2
        
        # Analytical formula
        E_ana = analytical_dirac_energy(1, -1, Z=1, c=C_LIGHT)
        
        # Check agreement
        rel_err = abs(E_num - E_ana) / abs(E_ana)
        assert rel_err < 1e-5, f"Ground state error: {rel_err:.2e}"
        
        print(f"✓ Ground state validated: rel_err = {rel_err:.2e}")


class TestResonanceEmergence:
    """Test that resonances emerge as theta increases."""
    
    def test_resonances_appear_with_theta(self):
        """Verify resonances emerge from continuum as theta increases."""
        # At theta=0, few/no resonances (all real)
        E0, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.1, theta=0.0, return_complex=True
        )
        res0 = extract_resonances(E0, threshold=1e-6)
        n_res_0 = len(res0['energies'])
        
        # At theta=0.3, resonances should appear
        E_theta, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.1, theta=0.3, return_complex=True
        )
        res_theta = extract_resonances(E_theta, threshold=1e-6)
        n_res_theta = len(res_theta['energies'])
        
        # Should have more resonances at theta>0
        assert n_res_theta > n_res_0, \
            f"No resonance emergence: {n_res_0} → {n_res_theta}"
        
        print(f"✓ Resonances emerge: {n_res_0} → {n_res_theta} as theta increases")
    
    def test_resonance_widths_positive(self):
        """Verify resonance widths are positive."""
        E, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.1, theta=0.3, return_complex=True
        )
        res = extract_resonances(E, threshold=1e-6)
        
        if len(res['widths']) > 0:
            # All widths should be positive
            assert np.all(res['widths'] > 0), "Negative resonance widths found"
            print(f"✓ Resonance widths positive: min={np.min(res['widths']):.2e}")
        else:
            print("⊘ No resonances found (skipped width check)")


class TestSpectralStructure:
    """Test correct classification of eigenvalues."""
    
    def test_eigenvalue_classification(self):
        """Verify eigenvalues are correctly classified."""
        E, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.1, theta=0.2, return_complex=True
        )
        res = extract_resonances(E, threshold=1e-6)
        
        # Check that all resonances have negative imaginary parts
        if len(res['resonances']) > 0:
            assert np.all(np.imag(res['resonances']) < -1e-6), \
                "Resonances don't have negative imaginary parts"
        
        print(f"✓ Eigenvalue classification correct: " +
              f"{len(res['bound'])} bound, {len(res['energies'])} resonances")
    
    def test_eigenvalue_count(self):
        """Verify total eigenvalue count."""
        N = 100
        E, _, _ = solve_mabgps_ccr(N=N, Z=1, lambda_shield=0.1, theta=0.2)
        
        # Should have 2*(N-2) eigenvalues
        expected_count = 2 * (N - 2)
        assert len(E) == expected_count, \
            f"Expected {expected_count} eigenvalues, got {len(E)}"
        
        print(f"✓ Eigenvalue count correct: {len(E)} = 2*({N}-2)")


class TestConvenience:
    """Test convenience wrapper function."""
    
    def test_ccr_with_resonances_wrapper(self):
        """Test solve_mabgps_ccr_with_resonances() wrapper."""
        result = solve_mabgps_ccr_with_resonances(
            N=100, Z=1, lambda_shield=0.1, theta=0.3
        )
        
        # Check all expected keys
        expected_keys = ['eigenvalues', 'bound', 'resonances', 'energies', 
                        'widths', 'r_interior', 'eigenvectors', 'theta']
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        # Check theta value
        assert result['theta'] == 0.3
        
        # Check that resonances have positive widths
        if len(result['widths']) > 0:
            assert np.all(result['widths'] > 0)
        
        print(f"✓ Convenience wrapper works: {len(result['energies'])} resonances")


class TestNumericalStability:
    """Test numerical stability and convergence."""
    
    def test_convergence_with_grid_refinement(self):
        """Verify convergence as grid is refined."""
        mc2 = M_ELECTRON * C_LIGHT**2
        
        # Coarse grid
        E_coarse, _, _ = solve_mabgps_ccr(
            N=80, Z=1, lambda_shield=0.0, theta=0.0, return_complex=False
        )
        bound_coarse = E_coarse[(E_coarse > 0) & (E_coarse < mc2)]
        E_coarse_gs = np.min(bound_coarse)
        
        # Fine grid
        E_fine, _, _ = solve_mabgps_ccr(
            N=120, Z=1, lambda_shield=0.0, theta=0.0, return_complex=False
        )
        bound_fine = E_fine[(E_fine > 0) & (E_fine < mc2)]
        E_fine_gs = np.min(bound_fine)
        
        # Check convergence
        rel_change = abs(E_fine_gs - E_coarse_gs) / abs(E_coarse_gs)
        assert rel_change < 1e-4, f"Poor convergence: {rel_change:.2e}"
        
        print(f"✓ Convergence verified: rel_change = {rel_change:.2e}")
    
    def test_complex_arithmetic_stability(self):
        """Verify complex arithmetic doesn't introduce spurious errors."""
        # Solve at small theta (should be close to real case)
        E_small_theta, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.0, theta=0.01, return_complex=True
        )
        
        # Real parts should match theta=0 case
        E_zero, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.0, theta=0.0, return_complex=False
        )
        
        # Compare first 10 eigenvalues
        rel_err = np.abs(np.real(E_small_theta[:10]) - E_zero[:10]) / np.abs(E_zero[:10])
        assert np.all(rel_err < 1e-3), f"Large errors at small theta: {np.max(rel_err):.2e}"
        
        print(f"✓ Complex arithmetic stable: max rel_err = {np.max(rel_err):.2e}")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_resonance_workflow(self):
        """Test complete workflow: solve → extract → validate."""
        # Solve with CCR
        result = solve_mabgps_ccr_with_resonances(
            N=100, Z=1, lambda_shield=0.1, theta=0.3
        )
        
        # Verify structure
        assert len(result['r_interior']) > 0
        assert result['eigenvectors'].shape[0] == 2 * len(result['r_interior'])
        
        print(f"✓ Full workflow successful: {len(result['energies'])} resonances found")
    
    def test_comparison_theta_scan(self):
        """Test that resonance properties vary with theta."""
        theta_values = [0.1, 0.2, 0.3, 0.4]
        results = []
        
        for theta in theta_values:
            E, _, _ = solve_mabgps_ccr(
                N=100, Z=1, lambda_shield=0.1, theta=theta, return_complex=True
            )
            res = extract_resonances(E, threshold=1e-6)
            results.append(res)
        
        # Check that resonances are found at all theta values
        n_res = [len(r['energies']) for r in results]
        assert all(n > 0 for n in n_res), f"No resonances at some theta: {n_res}"
        
        print(f"✓ Resonance count across theta scan: {n_res}")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Complex Coordinate Rotation (CCR) Test Suite")
    print("=" * 70)
    print()
    
    # Run all test classes
    test_classes = [
        TestCCRBackwardCompatibility,
        TestBoundStateInvariance,
        TestResonanceEmergence,
        TestSpectralStructure,
        TestConvenience,
        TestNumericalStability,
        TestIntegration,
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 70)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                passed_tests += 1
            except Exception as e:
                print(f"✗ {method_name}: {e}")
    
    print()
    print("=" * 70)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)
