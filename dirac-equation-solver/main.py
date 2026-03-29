"""Main entry point for Dirac equation solver comparison."""

import numpy as np

import config as cfg
from potential import analytical_dirac_energy
from bspline import solve_bspline
from mabgps import solve_mabgps
from plot import plot_spectrum, plot_wavefunctions


def main():
    mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2

    print("=" * 60)
    print("Dirac Equation Solver: MAB-GPS vs B-spline Comparison")
    print("=" * 60)
    print(f"Parameters: Z={cfg.Z}, lambda={cfg.LAMBDA_SHIELD}, N={cfg.N_POINTS}")
    print()

    print("Running B-spline solver...")
    E_bs = solve_bspline()
    print(f"  -> {len(E_bs)} eigenvalues computed")

    print("Running MAB-GPS solver...")
    E_mab, vecs_mab, r_mab = solve_mabgps()
    print(f"  -> {len(E_mab)} eigenvalues computed")
    print()

    print("-" * 60)
    print("Validation: MAB-GPS vs Analytical (lambda=0, unshielded)")
    print("-" * 60)

    E_mab_l0, _, _ = solve_mabgps(lambda_shield=0.0)
    bound_l0 = E_mab_l0[(E_mab_l0 > 0) & (E_mab_l0 < mc2)]
    E_num = np.min(bound_l0) / mc2
    E_ana = analytical_dirac_energy(1, -1, cfg.Z, cfg.C_LIGHT)
    rel_err = abs(E_num - E_ana) / abs(E_ana)

    print(f"  Ground state (n=1, kappa=-1, Z={cfg.Z}):")
    print(f"    Numerical:  {E_num:.10f} mc²")
    print(f"    Analytical: {E_ana:.10f} mc²")
    print(f"    Rel. error: {rel_err:.2e}")
    status = "PASS" if rel_err < 1e-6 else "FAIL"
    print(f"    Status:     {status} (threshold: 1e-6)")
    print()

    print("-" * 60)
    print("Energy Comparison: First 5 Bound States (lambda=0.1)")
    print("-" * 60)

    bound_mab = E_mab[(E_mab > 0) & (E_mab < mc2)]
    bound_mab_sorted = np.sort(bound_mab)[:5]

    bound_bs = E_bs[(E_bs > 0) & (E_bs < mc2)]
    bound_bs_sorted = np.sort(bound_bs)[:5]

    print(f"  {'State':<8} {'MAB-GPS (mc²)':<18} {'B-spline (mc²)':<18}")
    print(f"  {'-' * 8} {'-' * 18} {'-' * 18}")
    for i in range(min(5, len(bound_mab_sorted), len(bound_bs_sorted))):
        e_mab = bound_mab_sorted[i] / mc2 if i < len(bound_mab_sorted) else float("nan")
        e_bs = bound_bs_sorted[i] / mc2 if i < len(bound_bs_sorted) else float("nan")
        print(f"  {i + 1:<8} {e_mab:<18.6f} {e_bs:<18.6f}")
    print()

    print("-" * 60)
    print("Spurious State Analysis")
    print("-" * 60)

    mab_in_gap = len(E_mab[(E_mab > -mc2) & (E_mab < mc2)])
    bs_in_gap = len(E_bs[(E_bs > -mc2) & (E_bs < mc2)])

    print(f"  States in energy gap [-mc², +mc²]:")
    print(f"    MAB-GPS:  {mab_in_gap} (physical bound states only)")
    print(f"    B-spline: {bs_in_gap} (includes spurious states)")
    print()

    print("-" * 60)
    print("Generating Plots...")
    print("-" * 60)

    plot_spectrum(E_bs, E_mab, cfg.C_LIGHT, "spectrum.png")
    print("  Saved: spectrum.png")

    plot_wavefunctions(
        E_bs, None, None, E_mab, vecs_mab, r_mab, cfg.C_LIGHT, "wavefunction.png"
    )
    print("  Saved: wavefunction.png")
    print()

    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
