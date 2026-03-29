"""
MAB-GPS pseudospectral solver for the radial Dirac equation.

Uses Chebyshev-Gauss-Lobatto (CGL) collocation with algebraic mapping r(x) = L(1+x)/(1-x+alpha).
CGL nodes include both endpoints (x=-1, x=+1), enabling Dirichlet BC enforcement via truncation.
The interior nodes are extracted and assembled into the Hamiltonian, ensuring:
- P(0) = Q(0) = 0 (regularity at origin, enforced by truncation)
- P(r_max) = Q(r_max) = 0 (boundary wall, enforced by truncation)

Energy convention: TOTAL energy including rest mass.
"""

import numpy as np
from scipy import linalg

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


def solve_mabgps(
    N=N_POINTS,
    L=L_SCALE,
    alpha_map=ALPHA_MAP,
    Z=Z,
    lambda_shield=LAMBDA_SHIELD,
    kappa=KAPPA,
    c=C_LIGHT,
):
    """
    Solve radial Dirac equation using CGL pseudospectral method with boundary truncation.

    Uses Chebyshev-Gauss-Lobatto (CGL) nodes with algebraic mapping r(x) = L(1+x)/(1-x+alpha).
    Enforces Dirichlet boundary conditions via matrix truncation:
    - Interior nodes: x[1], ..., x[N-2] (excludes boundary nodes at x=-1 and x=+1)
    - Corresponding r values: r_interior excludes r=0 and r=r_max
    - Hamiltonian: assembled on interior nodes only (no symmetrization — preserves spectral accuracy)
    - Eigensolve: scipy.linalg.eig; imaginary parts are numerical noise at ~1e-14 and discarded via .real

    Args:
        N: Number of CGL nodes (includes endpoints).
        L: Scaling parameter for mapping.
        alpha_map: Mapping parameter (controls density near origin).
        Z: Nuclear charge.
        lambda_shield: Shielding parameter.
        kappa: Dirac quantum number.
        c: Speed of light (a.u.).

    Returns:
        tuple: (E_sorted, vecs_sorted, r_interior)
            - E_sorted: Real eigenvalues sorted by ascending value (2*(N-2) values)
            - vecs_sorted: Corresponding eigenvectors, shape (2*(N-2), 2*(N-2))
            - r_interior: Physical radial grid (interior nodes only, N-2 values, all > 0)
    """
    m = M_ELECTRON
    mc2 = m * c**2

    x_all = _cgl_nodes(N)

    r_all = L * (1 + x_all) / (1 - x_all + alpha_map)

    dr_dx_all = L * (2 + alpha_map) / (1 - x_all + alpha_map) ** 2
    dx_dr_all = 1.0 / dr_dx_all

    D_x = _cgl_deriv_matrix(x_all)

    D_r_all = np.diag(dx_dr_all) @ D_x

    interior_idx = np.arange(1, N - 1)
    r_interior = r_all[interior_idx]
    D_r_interior = D_r_all[np.ix_(interior_idx, interior_idx)]

    V_interior = V(r_interior, Z, lambda_shield)
    V_diag = np.diag(V_interior)
    kappa_over_r = np.diag(kappa / r_interior)

    N2 = len(r_interior)
    I_N2 = np.eye(N2)

    H = np.block(
        [
            [V_diag + mc2 * I_N2, c * (-D_r_interior + kappa_over_r)],
            [c * (D_r_interior + kappa_over_r), V_diag - mc2 * I_N2],
        ]
    )

    eigenvalues_complex, eigenvectors = linalg.eig(H)
    eigenvalues = eigenvalues_complex.real
    eigenvectors = eigenvectors.real

    sort_idx = np.argsort(eigenvalues)
    E_sorted = eigenvalues[sort_idx]
    vecs_sorted = eigenvectors[:, sort_idx]

    return E_sorted, vecs_sorted, r_interior
