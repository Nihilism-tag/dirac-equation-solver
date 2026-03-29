"""
Shielded Coulomb potential and analytical Dirac energy formula.

Energy convention: TOTAL energy including rest mass.
"""

import numpy as np
from config import M_ELECTRON


def V(r, Z, lambda_shield):
    """
    Shielded Coulomb potential: V(r) = -Z/r * exp(-lambda*r)

    Args:
        r: Radial coordinate (scalar or array). Atomic units.
        Z: Nuclear charge.
        lambda_shield: Shielding parameter.

    Returns:
        Potential value(s). Finite everywhere (r=0 protected).
    """
    # Protect against r=0 singularity using masking to avoid divide-by-zero warning
    r = np.asarray(r)
    result = np.empty_like(r, dtype=float)
    mask = r < 1e-15
    result[mask] = -Z * 1e15
    result[~mask] = -Z / r[~mask] * np.exp(-lambda_shield * r[~mask])
    return result if r.ndim > 0 else result.item()


def analytical_dirac_energy(n, kappa, Z, c):
    """
    Hydrogen-like Dirac analytical energy formula (total energy normalized to mc^2=1).

    Formula: E/mc^2 = [1 + (Z*alpha_fs / (n - |kappa| + sqrt(kappa^2 - (Z*alpha_fs)^2)))^2]^(-1/2)

    where alpha_fs = 1/c (fine-structure constant).

    Args:
        n: Principal quantum number (n >= 1).
        kappa: Dirac quantum number (kappa != 0).
        Z: Nuclear charge.
        c: Speed of light (atomic units).

    Returns:
        Total energy E normalized to mc^2=1 (includes rest mass).
    """
    alpha_fs = 1.0 / c
    denom = n - abs(kappa) + np.sqrt(kappa**2 - (Z * alpha_fs) ** 2)
    return (1.0 + (Z * alpha_fs / denom) ** 2) ** (-0.5)
