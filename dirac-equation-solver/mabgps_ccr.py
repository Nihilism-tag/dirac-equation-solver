"""
MAB-GPS pseudospectral solver with Complex Coordinate Rotation (CCR) support.

Extends mabgps.py to handle complex scaling transformation r → r·e^{iθ}.
Maintains backward compatibility: theta=0 recovers original solver.

Key modifications:
1. Accept theta parameter (default 0 for backward compatibility)
2. Apply CCR transformation to Hamiltonian matrix
3. Return complex eigenvalues (not forced to real)
4. Provide resonance extraction utilities

Energy convention: TOTAL energy including rest mass.
"""

import numpy as np
from scipy import linalg
from typing import Tuple, Optional

from config import (
    N_POINTS,
    L_SCALE,
    ALPHA_MAP,
    Z,
    LAMBDA_SHIELD,
    KAPPA,
    C_LIGHT,
    M_ELECTRON,
)
from potential import V
from complex_coordinate_rotation import V_complex, extract_resonances


def _cgl_nodes(N):
    """
    Chebyshev-Gauss-Lobatto nodes: x_k = -cos(k*pi/(N-1)), k=0,...,N-1.
    
    Properties:
    - Includes both endpoints: x[0] = -1, x[-1] = +1
    - Clustered near boundaries (suitable for boundary layer resolution)
    - Analytical formula (no iterative root finding)
    
    Args:
        N: Number of nodes.
    
    Returns:
        x: Array of N CGL nodes in [-1, 1].
    """
    k = np.arange(N)
    return -np.cos(np.pi * k / (N - 1))


def _cgl_deriv_matrix(x):
    """
    Chebyshev spectral derivative matrix for CGL nodes.
    
    Based on Trefethen (2000), "Spectral Methods in MATLAB", p. 53.
    
    D_ij = c_i/c_j * (-1)^(i+j) / (x_i - x_j)   for i != j
    D_ii = -sum_{j != i} D_ij
    
    where c_k = 2 for k=0 or k=N-1, and c_k = 1 otherwise.
    
    Args:
        x: Array of CGL nodes (length N, includes ±1).
    
    Returns:
        D: N x N derivative matrix.
    """
    N = len(x)
    c = np.ones(N)
    c[0] = 2.0
    c[-1] = 2.0
    
    D = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if i != j:
                D[i, j] = (c[i] / c[j]) * ((-1.0) ** (i + j)) / (x[i] - x[j])
    
    # Diagonal: sum rule
    for i in range(N):
        D[i, i] = -np.sum(D[i, :])
    
    return D


def solve_mabgps_ccr(
    N=N_POINTS,
    L=L_SCALE,
    alpha_map=ALPHA_MAP,
    Z=Z,
    lambda_shield=LAMBDA_SHIELD,
    kappa=KAPPA,
    c=C_LIGHT,
    theta: float = 0.0,
    return_complex: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Solve radial Dirac equation with Complex Coordinate Rotation (CCR).
    
    Extends solve_mabgps() to support complex scaling transformation r → r·e^{iθ}.
    For theta=0, recovers the original real eigenvalue problem.
    For theta>0, eigenvalues become complex, allowing resonance identification.
    
    Uses Chebyshev-Gauss-Lobatto (CGL) nodes with algebraic mapping r(x) = L(1+x)/(1-x+alpha).
    Enforces Dirichlet boundary conditions via matrix truncation:
    - Interior nodes: x[1], ..., x[N-2] (excludes boundary nodes at x=-1 and x=+1)
    - Corresponding r values: r_interior excludes r=0 and r=r_max
    - Hamiltonian: assembled on interior nodes only
    
    Args:
        N: Number of CGL nodes (includes endpoints).
        L: Scaling parameter for mapping.
        alpha_map: Mapping parameter (controls density near origin).
        Z: Nuclear charge.
        lambda_shield: Shielding parameter.
        kappa: Dirac quantum number.
        c: Speed of light (a.u.).
        theta: Complex rotation angle (radians). Default 0 (no rotation).
               Typical range: 0.1-0.5 for resonance identification.
        return_complex: If True, return complex eigenvalues. If False, return real parts.
    
    Returns:
        tuple: (E_sorted, vecs_sorted, r_interior)
            - E_sorted: Eigenvalues (complex if theta>0 and return_complex=True)
            - vecs_sorted: Corresponding eigenvectors, shape (2*(N-2), 2*(N-2))
            - r_interior: Physical radial grid (interior nodes only, N-2 values, all > 0)
    
    Notes:
        - For theta=0, eigenvalues are real (bound states + continuum)
        - For theta>0, resonances appear as complex eigenvalues with Im(E) < 0
        - Bound states remain real and independent of theta
        - Eigenvectors are complex for theta>0
    
    Example:
        >>> # Solve without complex scaling (original problem)
        >>> E_real, vecs, r = solve_mabgps_ccr(theta=0.0)
        >>> 
        >>> # Solve with complex scaling to find resonances
        >>> E_complex, vecs, r = solve_mabgps_ccr(theta=0.3)
        >>> resonances = extract_resonances(E_complex)
        >>> print(f"Found {len(resonances['energies'])} resonances")
    """
    m = M_ELECTRON
    mc2 = m * c**2
    
    # Generate CGL nodes and mapping
    x_all = _cgl_nodes(N)
    r_all = L * (1 + x_all) / (1 - x_all + alpha_map)
    
    dr_dx_all = L * (2 + alpha_map) / (1 - x_all + alpha_map) ** 2
    dx_dr_all = 1.0 / dr_dx_all
    
    # Spectral derivative matrix
    D_x = _cgl_deriv_matrix(x_all)
    D_r_all = np.diag(dx_dr_all) @ D_x
    
    # Extract interior nodes (enforce boundary conditions)
    interior_idx = np.arange(1, N - 1)
    r_interior = r_all[interior_idx]
    D_r_interior = D_r_all[np.ix_(interior_idx, interior_idx)]
    
    N2 = len(r_interior)
    I_N2 = np.eye(N2)
    
    # ========================================================================
    # COMPLEX COORDINATE ROTATION
    # ========================================================================
    
    if theta == 0.0:
        # Original real problem
        V_interior = V(r_interior, Z, lambda_shield)
        V_diag = np.diag(V_interior)
        kappa_over_r = np.diag(kappa / r_interior)
        
        H = np.block([
            [V_diag + mc2 * I_N2, c * (-D_r_interior + kappa_over_r)],
            [c * (D_r_interior + kappa_over_r), V_diag - mc2 * I_N2],
        ])
    else:
        # Complex-scaled problem: r → r·e^{iθ}
        scale_factor = np.exp(-1j * theta)
        
        # Evaluate potential at complex coordinate r·e^{iθ}
        r_complex = r_interior * np.exp(1j * theta)
        V_interior_complex = V_complex(r_complex, Z, lambda_shield)
        V_diag = np.diag(V_interior_complex)
        
        # Kinetic terms scale by e^{-iθ}
        kappa_over_r = np.diag(kappa / r_interior)
        K_upper = scale_factor * (-D_r_interior + kappa_over_r)
        K_lower = scale_factor * (D_r_interior + kappa_over_r)
        
        H = np.block([
            [V_diag + mc2 * I_N2, c * K_upper],
            [c * K_lower, V_diag - mc2 * I_N2],
        ])
    
    # ========================================================================
    # EIGENVALUE SOLVE
    # ========================================================================
    
    eigenvalues_complex, eigenvectors = linalg.eig(H)
    
    # For theta=0, discard imaginary parts (numerical noise)
    # For theta>0, keep complex eigenvalues
    if theta == 0.0 and not return_complex:
        eigenvalues = eigenvalues_complex.real
        eigenvectors = eigenvectors.real
    else:
        eigenvalues = eigenvalues_complex
        # Eigenvectors remain complex for theta>0
    
    # Sort by real part of eigenvalue
    sort_idx = np.argsort(np.real(eigenvalues))
    E_sorted = eigenvalues[sort_idx]
    vecs_sorted = eigenvectors[:, sort_idx]
    
    return E_sorted, vecs_sorted, r_interior


def solve_mabgps_ccr_with_resonances(
    N=N_POINTS,
    L=L_SCALE,
    alpha_map=ALPHA_MAP,
    Z=Z,
    lambda_shield=LAMBDA_SHIELD,
    kappa=KAPPA,
    c=C_LIGHT,
    theta: float = 0.3,
    resonance_threshold: float = 1e-6,
) -> dict:
    """
    Solve Dirac equation with CCR and automatically extract resonances.
    
    Convenience wrapper that combines solve_mabgps_ccr() and extract_resonances().
    
    Args:
        theta: Complex rotation angle (default 0.3 rad ≈ 17°)
        resonance_threshold: Threshold for identifying resonances
        **other args: Passed to solve_mabgps_ccr()
    
    Returns:
        Dictionary with keys:
        - 'eigenvalues': All complex eigenvalues
        - 'bound': Real parts of bound state eigenvalues
        - 'resonances': Complex resonance eigenvalues
        - 'energies': Real parts of resonance energies
        - 'widths': Resonance widths Γ = -2·Im(E)
        - 'r_interior': Radial grid
        - 'eigenvectors': Full eigenvector matrix
        - 'theta': The θ value used
    
    Example:
        >>> result = solve_mabgps_ccr_with_resonances(theta=0.3, Z=1, lambda_shield=0.1)
        >>> print(f"Resonances: {result['energies']}")
        >>> print(f"Widths: {result['widths']}")
    """
    E_complex, vecs, r = solve_mabgps_ccr(
        N=N, L=L, alpha_map=alpha_map, Z=Z, lambda_shield=lambda_shield,
        kappa=kappa, c=c, theta=theta, return_complex=True
    )
    
    resonance_data = extract_resonances(E_complex, threshold=resonance_threshold)
    
    return {
        'eigenvalues': E_complex,
        'bound': resonance_data['bound'],
        'resonances': resonance_data['resonances'],
        'energies': resonance_data['energies'],
        'widths': resonance_data['widths'],
        'r_interior': r,
        'eigenvectors': vecs,
        'theta': theta,
    }


if __name__ == "__main__":
    print("MAB-GPS CCR solver loaded successfully.")
    print("\nExample usage:")
    print("  from mabgps_ccr import solve_mabgps_ccr_with_resonances")
    print("  result = solve_mabgps_ccr_with_resonances(theta=0.3)")
    print("  print(result['energies'])  # Resonance energies")
    print("  print(result['widths'])    # Resonance widths")
