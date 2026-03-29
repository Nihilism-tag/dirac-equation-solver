"""
B-spline Galerkin solver for the radial Dirac equation.

This implementation intentionally violates kinetic balance by using the SAME
basis functions for both large (P) and small (Q) components, which produces
spurious states in the energy gap [-mc², +mc²].

Energy convention: TOTAL energy including rest mass.
"""

import numpy as np
from scipy import linalg
from scipy.interpolate import BSpline

from config import N_POINTS, R_MAX, Z, LAMBDA_SHIELD, KAPPA, C_LIGHT, M_ELECTRON
from potential import V


def _make_bspline_basis(N, r_max, k=5):
    """
    Create B-spline basis functions of order k on [0, r_max].

    Uses clamped knots at both ends and uniform interior knots.
    Returns basis functions that satisfy B_i(0) = B_i(r_max) = 0
    by excluding the first and last basis functions.

    Args:
        N: Number of interior basis functions to return.
        r_max: Domain upper bound.
        k: B-spline order (degree = k-1). Default 5 (quartic).

    Returns:
        List of (B_i, dB_i) tuples where B_i is the basis function
        and dB_i is its derivative.
    """
    # Number of interior knots needed for N basis functions
    # Total basis functions = n_knots + k - 1, we want N+2 (including boundary)
    # So n_interior = N + 2 - k + 1 = N - k + 3
    n_interior = N + 2

    # Create knot vector: k repeated 0s, uniform interior, k repeated r_max
    interior_knots = np.linspace(0, r_max, n_interior)
    knots = np.concatenate([np.zeros(k - 1), interior_knots, np.full(k - 1, r_max)])

    # Total number of basis functions
    n_basis = len(knots) - k

    # Create basis functions (exclude first and last for boundary conditions)
    basis = []
    for i in range(1, n_basis - 1):  # Skip first and last
        # Coefficient vector: 1 at position i, 0 elsewhere
        c = np.zeros(n_basis)
        c[i] = 1.0

        # Create B-spline and its derivative
        spl = BSpline(knots, c, k - 1)  # degree = k - 1
        dspl = spl.derivative()

        basis.append((spl, dspl))

    return basis[:N]  # Return exactly N basis functions


def solve_bspline(
    N=N_POINTS, r_max=R_MAX, Z=Z, lambda_shield=LAMBDA_SHIELD, kappa=KAPPA, c=C_LIGHT
):
    """
    Solve radial Dirac equation using B-spline Galerkin method.

    This method intentionally uses the SAME basis for P and Q components,
    violating kinetic balance and producing spurious states.

    Args:
        N: Number of basis functions.
        r_max: Domain upper bound (a.u.).
        Z: Nuclear charge.
        lambda_shield: Shielding parameter.
        kappa: Dirac quantum number.
        c: Speed of light (a.u.).

    Returns:
        np.ndarray: All 2N eigenvalues (sorted), including spurious states.
    """
    m = M_ELECTRON
    mc2 = m * c**2

    # Get B-spline basis functions
    basis = _make_bspline_basis(N, r_max, k=5)
    n_basis = len(basis)

    # Gauss-Legendre quadrature on [0, r_max]
    n_quad = 4 * N
    x_gl, w_gl = np.polynomial.legendre.leggauss(n_quad)

    # Map from [-1, 1] to [0, r_max]
    r_quad = 0.5 * r_max * (x_gl + 1)
    w_quad = 0.5 * r_max * w_gl

    # Evaluate potential at quadrature points
    V_quad = V(r_quad, Z, lambda_shield)

    # Evaluate all basis functions and derivatives at quadrature points
    B_vals = np.zeros((n_basis, n_quad))
    dB_vals = np.zeros((n_basis, n_quad))

    for i, (B_i, dB_i) in enumerate(basis):
        B_vals[i, :] = B_i(r_quad)
        dB_vals[i, :] = dB_i(r_quad)

    # Build matrices using numerical integration
    # S_ij = ∫ B_i(r) B_j(r) dr
    # H_PP_ij = ∫ B_i(r) (V(r) + mc²) B_j(r) dr
    # H_QQ_ij = ∫ B_i(r) (V(r) - mc²) B_j(r) dr
    # H_PQ_ij = ∫ B_i(r) c(-d/dr + κ/r) B_j(r) dr
    # H_QP_ij = ∫ B_i(r) c(d/dr + κ/r) B_j(r) dr

    S_block = np.zeros((n_basis, n_basis))
    H_PP = np.zeros((n_basis, n_basis))
    H_QQ = np.zeros((n_basis, n_basis))
    H_PQ = np.zeros((n_basis, n_basis))
    H_QP = np.zeros((n_basis, n_basis))

    # Precompute κ/r (with protection for r~0)
    kappa_over_r = np.where(r_quad > 1e-15, kappa / r_quad, 0.0)

    for i in range(n_basis):
        for j in range(n_basis):
            # Overlap integral
            integrand_S = B_vals[i, :] * B_vals[j, :] * w_quad
            S_block[i, j] = np.sum(integrand_S)

            # H_PP: (V + mc²) diagonal block
            integrand_PP = B_vals[i, :] * (V_quad + mc2) * B_vals[j, :] * w_quad
            H_PP[i, j] = np.sum(integrand_PP)

            # H_QQ: (V - mc²) diagonal block
            integrand_QQ = B_vals[i, :] * (V_quad - mc2) * B_vals[j, :] * w_quad
            H_QQ[i, j] = np.sum(integrand_QQ)

            # H_PQ: c(-d/dr + κ/r) off-diagonal block
            # ∫ B_i * c * (-dB_j/dr + κ/r * B_j) dr
            integrand_PQ = (
                B_vals[i, :]
                * c
                * (-dB_vals[j, :] + kappa_over_r * B_vals[j, :])
                * w_quad
            )
            H_PQ[i, j] = np.sum(integrand_PQ)

            # H_QP: c(d/dr + κ/r) off-diagonal block
            # ∫ B_i * c * (dB_j/dr + κ/r * B_j) dr
            integrand_QP = (
                B_vals[i, :]
                * c
                * (dB_vals[j, :] + kappa_over_r * B_vals[j, :])
                * w_quad
            )
            H_QP[i, j] = np.sum(integrand_QP)

    # Assemble 2N × 2N block matrices
    # H = [[H_PP, H_PQ], [H_QP, H_QQ]]
    # S = [[S_block, 0], [0, S_block]]
    H = np.block([[H_PP, H_PQ], [H_QP, H_QQ]])

    S = np.block(
        [
            [S_block, np.zeros((n_basis, n_basis))],
            [np.zeros((n_basis, n_basis)), S_block],
        ]
    )

    # Solve generalized eigenvalue problem H c = E S c
    eigenvalues, _ = linalg.eigh(H, S)

    # Return sorted eigenvalues (eigh already returns sorted)
    return eigenvalues


def get_bspline_wavefunctions(
    N=N_POINTS, r_max=R_MAX, Z=Z, lambda_shield=LAMBDA_SHIELD, kappa=KAPPA, c=C_LIGHT
):
    """
    Solve and return eigenvectors for wavefunction plotting.

    Returns:
        tuple: (eigenvalues, eigenvectors, r_grid, basis)
            - eigenvalues: 2N sorted energies
            - eigenvectors: 2N × 2N matrix of coefficients
            - r_grid: radial grid for plotting
            - basis: list of basis functions
    """
    m = M_ELECTRON
    mc2 = m * c**2

    # Get B-spline basis functions
    basis = _make_bspline_basis(N, r_max, k=5)
    n_basis = len(basis)

    # Gauss-Legendre quadrature on [0, r_max]
    n_quad = 4 * N
    x_gl, w_gl = np.polynomial.legendre.leggauss(n_quad)

    # Map from [-1, 1] to [0, r_max]
    r_quad = 0.5 * r_max * (x_gl + 1)
    w_quad = 0.5 * r_max * w_gl

    # Evaluate potential at quadrature points
    V_quad = V(r_quad, Z, lambda_shield)

    # Evaluate all basis functions and derivatives at quadrature points
    B_vals = np.zeros((n_basis, n_quad))
    dB_vals = np.zeros((n_basis, n_quad))

    for i, (B_i, dB_i) in enumerate(basis):
        B_vals[i, :] = B_i(r_quad)
        dB_vals[i, :] = dB_i(r_quad)

    # Build matrices (same as solve_bspline)
    S_block = np.zeros((n_basis, n_basis))
    H_PP = np.zeros((n_basis, n_basis))
    H_QQ = np.zeros((n_basis, n_basis))
    H_PQ = np.zeros((n_basis, n_basis))
    H_QP = np.zeros((n_basis, n_basis))

    kappa_over_r = np.where(r_quad > 1e-15, kappa / r_quad, 0.0)

    for i in range(n_basis):
        for j in range(n_basis):
            integrand_S = B_vals[i, :] * B_vals[j, :] * w_quad
            S_block[i, j] = np.sum(integrand_S)

            integrand_PP = B_vals[i, :] * (V_quad + mc2) * B_vals[j, :] * w_quad
            H_PP[i, j] = np.sum(integrand_PP)

            integrand_QQ = B_vals[i, :] * (V_quad - mc2) * B_vals[j, :] * w_quad
            H_QQ[i, j] = np.sum(integrand_QQ)

            integrand_PQ = (
                B_vals[i, :]
                * c
                * (-dB_vals[j, :] + kappa_over_r * B_vals[j, :])
                * w_quad
            )
            H_PQ[i, j] = np.sum(integrand_PQ)

            integrand_QP = (
                B_vals[i, :]
                * c
                * (dB_vals[j, :] + kappa_over_r * B_vals[j, :])
                * w_quad
            )
            H_QP[i, j] = np.sum(integrand_QP)

    H = np.block([[H_PP, H_PQ], [H_QP, H_QQ]])

    S = np.block(
        [
            [S_block, np.zeros((n_basis, n_basis))],
            [np.zeros((n_basis, n_basis)), S_block],
        ]
    )

    # Solve with eigenvectors
    eigenvalues, eigenvectors = linalg.eigh(H, S)

    # Create radial grid for plotting
    r_grid = np.linspace(0.01, r_max, 500)

    return eigenvalues, eigenvectors, r_grid, basis
