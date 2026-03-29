"""
Complex Coordinate Rotation (CCR) module for resonance state identification.

Implements the complex scaling transformation r → r·e^{iθ} for the radial Dirac equation.
This allows resonance states (embedded in the continuum at θ=0) to become isolated
eigenvalues in the complex energy plane as θ increases.

Mathematical Framework:
======================

1. COORDINATE TRANSFORMATION
   r → r·e^{iθ}  where θ ∈ [0, π/4]

2. HAMILTONIAN TRANSFORMATION
   The radial Dirac Hamiltonian transforms as:
   
   H(θ) = [[V(r·e^{iθ}) + mc², c·e^{-iθ}(-d/dr + κ/r)],
           [c·e^{-iθ}(d/dr + κ/r),  V(r·e^{iθ}) - mc²]]
   
   Key insight: Off-diagonal kinetic terms scale by e^{-iθ}

3. SPECTRAL STRUCTURE
   - Bound states: Real eigenvalues, independent of θ
   - Resonances: Complex eigenvalues E = E_R - i·Γ/2
     * Emerge from continuum as θ increases
     * Γ = -2·Im(E) is the resonance width
   - Continuum: Rotates into complex plane, away from real axis

4. RESONANCE EXTRACTION
   For each eigenvalue E:
   - If |Im(E)| < threshold: Bound state or numerical noise
   - If Im(E) < -threshold: Resonance (width Γ = -2·Im(E))
   - If Im(E) > threshold: Unphysical (discard)

References:
===========
- Šeba, P. (1988). "The complex scaling method for Dirac resonances"
  Letters in Mathematical Physics 16, 39-46
- Alhaidari, A. D. (2007). "Relativistic extension of the complex scaling method"
  Phys. Rev. A 75, 042707
- Moiseyev, N. (1998). "Quantum theory of resonances"
  Physics Reports 302, 212-293
"""

import numpy as np
from scipy import linalg
from typing import Tuple, Dict, List


def apply_ccr_transformation(
    H_real: np.ndarray,
    r_interior: np.ndarray,
    theta: float,
    kappa: float,
    c: float,
    V_func,
    Z: float,
    lambda_shield: float,
) -> np.ndarray:
    """
    Apply complex coordinate rotation to the Hamiltonian matrix.
    
    Transforms the real Hamiltonian H(θ=0) into the complex-scaled version H(θ)
    by modifying the off-diagonal kinetic terms.
    
    Args:
        H_real: Original real Hamiltonian matrix (2N×2N), from mabgps.solve_mabgps()
        r_interior: Interior radial grid points (N values)
        theta: Complex rotation angle (radians), typically 0.1-0.5
        kappa: Dirac quantum number
        c: Speed of light (a.u.)
        V_func: Potential function V(r, Z, lambda_shield)
        Z: Nuclear charge
        lambda_shield: Shielding parameter
    
    Returns:
        H_ccr: Complex-scaled Hamiltonian matrix (2N×2N)
    
    Notes:
        - The transformation is applied to the kinetic energy terms only
        - The potential V(r) is evaluated at r·e^{iθ} (complex argument)
        - Off-diagonal blocks scale by e^{-iθ}
    """
    N = len(r_interior)
    
    # Complex scaling factor for kinetic terms
    scale_factor = np.exp(-1j * theta)
    
    # Extract blocks from original Hamiltonian
    # H_real = [[V + mc², c·(-D + κ/r)],
    #           [c·(D + κ/r),  V - mc²]]
    
    V_diag_plus = H_real[:N, :N] - np.eye(N)  # Remove mc² to get V + mc²
    V_diag_minus = H_real[N:, N:] + np.eye(N)  # Remove -mc² to get V - mc²
    
    # Kinetic terms (off-diagonal blocks)
    K_upper = H_real[:N, N:] / c  # c·(-D + κ/r) → (-D + κ/r)
    K_lower = H_real[N:, :N] / c  # c·(D + κ/r) → (D + κ/r)
    
    # Apply complex scaling to kinetic terms
    K_upper_ccr = scale_factor * K_upper
    K_lower_ccr = scale_factor * K_lower
    
    # Evaluate potential at complex coordinate r·e^{iθ}
    r_complex = r_interior * np.exp(1j * theta)
    V_complex = V_func(r_complex, Z, lambda_shield)
    V_diag_complex = np.diag(V_complex)
    
    # Construct complex-scaled Hamiltonian
    mc2 = 1.0  # In atomic units with m=1, c=137.036
    H_ccr = np.block([
        [V_diag_complex + mc2 * np.eye(N), c * K_upper_ccr],
        [c * K_lower_ccr, V_diag_complex - mc2 * np.eye(N)]
    ])
    
    return H_ccr


def extract_resonances(
    eigenvalues: np.ndarray,
    threshold: float = 1e-6,
) -> Dict[str, np.ndarray]:
    """
    Extract resonance states from complex eigenvalue spectrum.
    
    Classifies eigenvalues based on their imaginary part:
    - Bound states: |Im(E)| < threshold (real eigenvalues)
    - Resonances: Im(E) < -threshold (complex with negative imaginary part)
    - Unphysical: Im(E) > threshold (discard)
    
    Args:
        eigenvalues: Complex eigenvalue array from linalg.eig()
        threshold: Threshold for distinguishing bound states from resonances
    
    Returns:
        Dictionary with keys:
        - 'bound': Real parts of bound state eigenvalues
        - 'resonances': Complex resonance eigenvalues
        - 'widths': Resonance widths Γ = -2·Im(E)
        - 'energies': Real parts of resonance energies
        - 'all_complex': All eigenvalues (for debugging)
    
    Notes:
        - Resonance width is extracted as Γ = -2·Im(E_res)
        - Bound states have Im(E) ≈ 0 (numerical noise)
        - Physical resonances have Im(E) < 0
    """
    im_E = np.imag(eigenvalues)
    re_E = np.real(eigenvalues)
    
    # Classify eigenvalues
    bound_mask = np.abs(im_E) < threshold
    resonance_mask = im_E < -threshold
    
    bound_states = re_E[bound_mask]
    resonance_evals = eigenvalues[resonance_mask]
    
    # Extract resonance properties
    resonance_energies = np.real(resonance_evals)
    resonance_widths = -2.0 * np.imag(resonance_evals)
    
    # Sort by energy
    sort_idx = np.argsort(resonance_energies)
    
    return {
        'bound': np.sort(bound_states),
        'resonances': resonance_evals[sort_idx],
        'energies': resonance_energies[sort_idx],
        'widths': resonance_widths[sort_idx],
        'all_complex': eigenvalues,
    }


def scan_theta_resonances(
    solve_func,
    theta_values: np.ndarray,
    **solve_kwargs
) -> Dict[float, Dict]:
    """
    Scan resonance spectrum as function of complex rotation angle θ.
    
    For each θ value, solves the complex-scaled Dirac equation and extracts
    resonance states. Useful for visualizing resonance emergence and tracking
    resonance trajectories in the complex energy plane.
    
    Args:
        solve_func: Function that solves CCR-modified Dirac equation
                   Signature: solve_func(theta, **kwargs) → (E_complex, vecs, r)
        theta_values: Array of θ values to scan (e.g., np.linspace(0, 0.5, 20))
        **solve_kwargs: Additional arguments passed to solve_func
    
    Returns:
        Dictionary mapping θ → resonance data:
        {
            theta_1: {'energies': [...], 'widths': [...], 'all_evals': [...]},
            theta_2: {...},
            ...
        }
    
    Example:
        >>> theta_scan = np.linspace(0, 0.3, 15)
        >>> results = scan_theta_resonances(solve_ccr_dirac, theta_scan, Z=1, lambda_shield=0.1)
        >>> for theta, data in results.items():
        ...     print(f"θ={theta:.3f}: {len(data['energies'])} resonances")
    """
    results = {}
    
    for theta in theta_values:
        try:
            E_complex, vecs, r = solve_func(theta=theta, **solve_kwargs)
            resonance_data = extract_resonances(E_complex)
            results[theta] = resonance_data
        except Exception as e:
            print(f"Warning: Failed to solve at θ={theta}: {e}")
            results[theta] = None
    
    return results


def compute_resonance_trajectory(
    scan_results: Dict[float, Dict],
    resonance_index: int = 0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract trajectory of a single resonance in complex energy plane.
    
    Tracks how a specific resonance (identified by index) moves in the
    complex energy plane as θ varies. Useful for visualizing resonance
    emergence from continuum.
    
    Args:
        scan_results: Output from scan_theta_resonances()
        resonance_index: Which resonance to track (0=lowest energy, etc.)
    
    Returns:
        (theta_values, energies, widths): Arrays for plotting
        - theta_values: θ values where resonance was found
        - energies: Real parts E_R(θ)
        - widths: Widths Γ(θ)
    
    Notes:
        - Assumes resonances are ordered by energy at each θ
        - May fail if resonance index doesn't exist at all θ values
    """
    theta_vals = []
    energies = []
    widths = []
    
    for theta in sorted(scan_results.keys()):
        data = scan_results[theta]
        if data is None or len(data['energies']) <= resonance_index:
            continue
        
        theta_vals.append(theta)
        energies.append(data['energies'][resonance_index])
        widths.append(data['widths'][resonance_index])
    
    return np.array(theta_vals), np.array(energies), np.array(widths)


def validate_ccr_bound_states(
    E_theta_0: np.ndarray,
    E_theta_nonzero: np.ndarray,
    tolerance: float = 1e-6,
) -> bool:
    """
    Validate that bound states are invariant under complex scaling.
    
    Bound states should have the same energy regardless of θ (they are
    not affected by complex scaling). This function checks that the
    bound state energies match between θ=0 and θ>0.
    
    Args:
        E_theta_0: Bound state energies at θ=0
        E_theta_nonzero: Bound state energies at θ>0
        tolerance: Relative tolerance for energy matching
    
    Returns:
        True if bound states are invariant (within tolerance), False otherwise
    
    Notes:
        - Bound states should be identified before calling this function
        - Useful for verifying correct CCR implementation
    """
    if len(E_theta_0) != len(E_theta_nonzero):
        return False
    
    E_theta_0_sorted = np.sort(E_theta_0)
    E_theta_nonzero_sorted = np.sort(E_theta_nonzero)
    
    rel_errors = np.abs(E_theta_0_sorted - E_theta_nonzero_sorted) / np.abs(E_theta_0_sorted)
    
    return np.all(rel_errors < tolerance)


# ============================================================================
# HELPER: Extend potential.py to handle complex arguments
# ============================================================================

def V_complex(r_complex: np.ndarray, Z: float, lambda_shield: float) -> np.ndarray:
    """
    Shielded Coulomb potential for complex radial coordinate.
    
    Evaluates V(r) = -Z/r · exp(-λ·r) for complex r.
    
    Args:
        r_complex: Complex radial coordinate (scalar or array)
        Z: Nuclear charge
        lambda_shield: Shielding parameter
    
    Returns:
        Complex potential value(s)
    
    Notes:
        - Handles complex division and exponentials correctly
        - No singularity protection needed (complex r ≠ 0)
    """
    r_complex = np.asarray(r_complex, dtype=complex)
    return -Z / r_complex * np.exp(-lambda_shield * r_complex)


if __name__ == "__main__":
    # Example usage (requires mabgps module)
    print("Complex Coordinate Rotation module loaded successfully.")
    print("Use: from complex_coordinate_rotation import *")
