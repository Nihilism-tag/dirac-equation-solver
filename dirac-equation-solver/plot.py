"""Visualization for Dirac equation solver comparison."""

import numpy as np
import matplotlib.pyplot as plt

from config import M_ELECTRON, C_LIGHT


def plot_spectrum(E_bspline, E_mabgps, c=C_LIGHT, save_path="spectrum.png"):
    """
    Plot eigenvalue spectrum comparison between B-spline and MAB-GPS methods.

    Args:
        E_bspline: Eigenvalues from B-spline method (atomic units).
        E_mabgps: Eigenvalues from MAB-GPS method (atomic units).
        c: Speed of light (atomic units).
        save_path: Output file path.
    """
    mc2 = M_ELECTRON * c**2

    fig, ax = plt.subplots(figsize=(10, 6))

    idx_bs = np.arange(len(E_bspline))
    idx_mab = np.arange(len(E_mabgps))

    ax.scatter(
        idx_bs,
        E_bspline / mc2,
        c="red",
        marker="o",
        s=15,
        label="B-spline (with spurious)",
        alpha=0.7,
    )
    ax.scatter(
        idx_mab,
        E_mabgps / mc2,
        c="blue",
        marker="^",
        s=15,
        label="MAB-GPS (clean)",
        alpha=0.7,
    )

    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=1, label=r"$+mc^2$")
    ax.axhline(y=-1.0, color="gray", linestyle="--", linewidth=1, label=r"$-mc^2$")

    ax.set_ylim(-2, 2)
    ax.set_xlabel("Eigenvalue index")
    ax.set_ylabel(r"Energy $E/mc^2$")
    ax.set_title("Dirac Equation Eigenvalue Spectrum: B-spline vs MAB-GPS")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_wavefunctions(
    E_bs, vecs_bs, r_bs, E_mab, vecs_mab, r_mab, c=C_LIGHT, save_path="wavefunction.png"
):
    """
    Plot wavefunction comparison: B-spline spurious state vs MAB-GPS ground state.

    Args:
        E_bs: B-spline eigenvalues.
        vecs_bs: B-spline eigenvectors (not used directly, need basis evaluation).
        r_bs: B-spline radial grid.
        E_mab: MAB-GPS eigenvalues.
        vecs_mab: MAB-GPS eigenvectors (columns).
        r_mab: MAB-GPS radial grid.
        c: Speed of light.
        save_path: Output file path.
    """
    mc2 = M_ELECTRON * c**2
    N_mab = len(r_mab)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: B-spline - find a spurious state in the gap (near zero energy)
    gap_mask = (E_bs > -mc2) & (E_bs < mc2) & (E_bs < 0)
    if np.any(gap_mask):
        spurious_idx = np.where(gap_mask)[0][0]
        ax1.text(
            0.5,
            0.5,
            f"Spurious state index: {spurious_idx}\n"
            f"E = {E_bs[spurious_idx] / mc2:.4f} mc²\n\n"
            "(B-spline wavefunction requires\n"
            "basis function evaluation)",
            ha="center",
            va="center",
            transform=ax1.transAxes,
            fontsize=10,
        )
    else:
        ax1.text(
            0.5,
            0.5,
            "No negative spurious states found\nin gap for this configuration",
            ha="center",
            va="center",
            transform=ax1.transAxes,
            fontsize=10,
        )
    ax1.set_xlabel("r (a.u.)")
    ax1.set_ylabel("P(r)")
    ax1.set_title("B-spline: Spurious State")
    ax1.set_xlim(0, 20)

    # Right: MAB-GPS ground state
    bound_mask = (E_mab > 0) & (E_mab < mc2)
    if np.any(bound_mask):
        bound_indices = np.where(bound_mask)[0]
        ground_idx = bound_indices[np.argmin(E_mab[bound_mask])]

        N2 = N_mab
        P_ground = vecs_mab[:N2, ground_idx].real
        P_ground = P_ground / np.max(np.abs(P_ground))

        sort_idx = np.argsort(r_mab)
        r_sorted = r_mab[sort_idx]
        P_sorted = P_ground[sort_idx]

        plot_mask = r_sorted < 20
        ax2.plot(r_sorted[plot_mask], P_sorted[plot_mask], "b-", linewidth=1.5)
        ax2.set_title(f"MAB-GPS: Ground State (E = {E_mab[ground_idx] / mc2:.4f} mc²)")
    else:
        ax2.text(
            0.5,
            0.5,
            "No bound states found",
            ha="center",
            va="center",
            transform=ax2.transAxes,
        )
        ax2.set_title("MAB-GPS: Ground State")

    ax2.set_xlabel("r (a.u.)")
    ax2.set_ylabel("P(r) (normalized)")
    ax2.set_xlim(0, 20)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
