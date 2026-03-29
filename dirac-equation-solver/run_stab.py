"""Entry point for resonance state search via stabilization method."""

import matplotlib

matplotlib.use("Agg")

import config as cfg
from stab_scan import scan_stabilization, track_levels, find_resonance
from stab_plot import plot_stabilization_graph, plot_resonance_wavefunction


def main():
    mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2

    print("=" * 60)
    print("Stabilization Method: Resonance State Search")
    print("=" * 60)
    print(
        f"Parameters: Z={cfg.Z}, kappa={cfg.KAPPA}, lambda={cfg.LAMBDA_SHIELD}, N={cfg.N_POINTS}"
    )
    print(f"L scan: 0.5 to 3.0, step 0.05  ({int((3.0 - 0.5) / 0.05) + 1} L values)")
    print(f"Energy window: [0.9, 1.2] mc²")
    print()

    print("Phase 1: Scanning L_scale...")
    scan_result = scan_stabilization()
    total_levels = sum(len(e) for e in scan_result["eigenvalue_sets"])
    print(
        f"  -> {total_levels} total eigenvalues collected across {len(scan_result['L_arr'])} L values"
    )
    print()

    print("Phase 2: Tracking levels and identifying resonance plateau...")
    trajectories = track_levels(scan_result)
    E_res, L_opt, res_idx = find_resonance(scan_result["L_arr"], trajectories, mc2)

    if E_res is not None:
        print(
            f"  -> Resonance found: E_res = {E_res / mc2:.6f} mc²  ({E_res:.2f} a.u.)"
        )
        print(f"  -> Optimal scale:   L_opt = {L_opt:.4f}")
    else:
        print("  -> WARNING: No resonance plateau found in the energy window.")
        print("     Figures will be saved with placeholder messages.")
    print()

    print("Phase 3: Generating figures...")
    plot_stabilization_graph(scan_result["L_arr"], trajectories, res_idx, mc2)
    print("  -> Saved: fig_stabilization.png")

    plot_resonance_wavefunction(L_opt, E_res)
    print("  -> Saved: fig_resonance_wf.png")
    print()

    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
