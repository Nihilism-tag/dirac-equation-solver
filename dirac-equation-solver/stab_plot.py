"""Visualization for stabilization method: stabilization graph and resonance wavefunction."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import M_ELECTRON, C_LIGHT, Z, LAMBDA_SHIELD, KAPPA
from potential import V
from mabgps import solve_mabgps


def plot_stabilization_graph(
    L_arr,
    trajectories,
    res_idx,
    mc2,
    save_path="fig_stabilization.png",
):
    fig, ax = plt.subplots(figsize=(10, 6))

    for j in range(trajectories.shape[1]):
        col = np.ma.masked_invalid(trajectories[:, j] / mc2)
        if j == res_idx:
            continue
        ax.plot(
            L_arr,
            col,
            color="lightgray",
            linewidth=0.8,
            alpha=0.7,
            zorder=1,
        )

    if res_idx is not None and res_idx < trajectories.shape[1]:
        res_col = np.ma.masked_invalid(trajectories[:, res_idx] / mc2)
        valid = ~np.ma.getmaskarray(res_col)
        E_res_mc2 = float(np.mean(res_col.compressed()))
        ax.plot(
            L_arr,
            res_col,
            color="red",
            linewidth=2.5,
            zorder=3,
            label=f"Resonance ($E = {E_res_mc2:.4f}\\,mc^2$)",
        )
        ax.axhline(
            y=E_res_mc2,
            color="red",
            linestyle="--",
            linewidth=1.0,
            alpha=0.5,
            zorder=2,
        )
        ax.annotate(
            f"$E_{{res}} = {E_res_mc2:.4f}\\,mc^2$",
            xy=(L_arr[len(L_arr) // 2], E_res_mc2),
            xytext=(10, 8),
            textcoords="offset points",
            fontsize=9,
            color="red",
        )
        ax.legend(loc="upper right")
    else:
        ax.text(
            0.5,
            0.5,
            "No resonance found",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
            color="gray",
        )

    ax.set_xlabel(r"Scaling parameter $L_{scale}$ (a.u.)")
    ax.set_ylabel(r"Energy $E/mc^2$")
    ax.set_title(
        "Stabilization Graph: Resonance State in Shielded Coulomb Potential (Z=92)"
    )
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_resonance_wavefunction(
    L_opt,
    E_res,
    save_path="fig_resonance_wf.png",
    kappa=KAPPA,
    Z=Z,
    lambda_shield=LAMBDA_SHIELD,
    c=C_LIGHT,
):
    if L_opt is None or E_res is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(
            0.5,
            0.5,
            "Resonance not identified\n— run with broader scan parameters",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
            color="gray",
        )
        plt.tight_layout()
        plt.savefig(save_path, dpi=150)
        plt.close()
        return

    mc2 = M_ELECTRON * c**2

    E_arr, vecs, r_interior = solve_mabgps(
        L=L_opt, kappa=kappa, Z=Z, lambda_shield=lambda_shield, c=c
    )
    res_idx_local = np.argmin(np.abs(E_arr - E_res))
    N2 = len(r_interior)
    P = vecs[:N2, res_idx_local]
    P = np.abs(P)
    P = P / np.max(P)

    r_plot = r_interior[r_interior > 0.05]
    V_pot = V(r_plot, Z=Z, lambda_shield=lambda_shield)
    # Non-relativistic effective potential proxy normalized to mc²:
    # V_eff = [V(r) + κ(κ+1)/(2r²)] / mc²
    V_cent = kappa * (kappa + 1) / (2 * r_plot**2)
    V_eff = (V_pot + V_cent) / mc2

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(r_interior, P, "b-", linewidth=2, label=r"$P(r)$ large component")
    ax1.set_xlim(0, 20)

    ax2.plot(r_plot, V_eff, "g--", linewidth=1.5, label=r"$V_{eff}(r)/mc^2$")
    ax2.axhline(
        y=E_res / mc2,
        color="orange",
        linestyle=":",
        linewidth=1.5,
        label=f"$E_{{res}}/mc^2 = {E_res / mc2:.4f}$",
    )

    P_sq = P**2
    pocket_mask = P_sq > 0.1 * np.max(P_sq)
    if np.any(pocket_mask):
        r_inner = r_interior[pocket_mask][0]
        r_outer = r_interior[pocket_mask][-1]
        ax1.axvspan(
            r_inner,
            r_outer,
            alpha=0.1,
            color="blue",
            label="Wavefunction pocket",
        )

    ax1.set_xlabel("r (a.u.)")
    ax1.set_ylabel(r"$P(r)$ (normalized)", color="b")
    ax2.set_ylabel(r"$V_{eff}(r)/mc^2$", color="g")
    ax1.set_title(
        f"Resonance State Wavefunction ($E = {E_res / mc2:.4f}\\,mc^2$,"
        f"  $L_{{opt}} = {L_opt:.3f}$)"
    )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
