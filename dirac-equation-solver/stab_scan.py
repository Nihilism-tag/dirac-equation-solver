"""Stabilization method: L-scale scan, level tracking, and resonance detection."""

import numpy as np

from config import (
    N_POINTS,
    ALPHA_MAP,
    Z,
    LAMBDA_SHIELD,
    KAPPA,
    C_LIGHT,
    M_ELECTRON,
)
from mabgps import solve_mabgps


def scan_stabilization(
    L_min=0.5,
    L_max=3.0,
    L_step=0.05,
    E_min_frac=0.9,
    E_max_frac=1.2,
    N=N_POINTS,
    alpha_map=ALPHA_MAP,
    Z=Z,
    lambda_shield=LAMBDA_SHIELD,
    kappa=KAPPA,
    c=C_LIGHT,
):
    mc2 = M_ELECTRON * c**2
    L_arr = np.arange(L_min, L_max + L_step / 2, L_step)
    eigenvalue_sets = []

    for i, L in enumerate(L_arr):
        E, _, _ = solve_mabgps(
            N=N,
            L=L,
            alpha_map=alpha_map,
            Z=Z,
            lambda_shield=lambda_shield,
            kappa=kappa,
            c=c,
        )
        E_win = E[(E >= E_min_frac * mc2) & (E <= E_max_frac * mc2)]
        eigenvalue_sets.append(E_win)
        if i % 10 == 0:
            print(f"  L={L:.3f}: {len(E_win)} levels in window")

    return {"L_arr": L_arr, "eigenvalue_sets": eigenvalue_sets, "mc2": mc2}


def track_levels(scan_result):
    L_arr = scan_result["L_arr"]
    eigenvalue_sets = scan_result["eigenvalue_sets"]
    mc2 = scan_result["mc2"]
    n_L = len(L_arr)

    first_nonempty = next(
        (i for i, e in enumerate(eigenvalue_sets) if len(e) > 0), None
    )
    if first_nonempty is None:
        return np.full((n_L, 0), np.nan)

    tracks = list(np.sort(eigenvalue_sets[first_nonempty]))
    n_tracks = len(tracks)
    trajectories = np.full((n_L, n_tracks), np.nan)

    for j, v in enumerate(tracks):
        trajectories[first_nonempty, j] = v

    threshold = (
        0.5 * mc2 * (L_arr[1] - L_arr[0]) if len(L_arr) > 1 else 0.5 * mc2 * 0.05
    )

    for i in range(first_nonempty + 1, n_L):
        new_eigs = np.sort(eigenvalue_sets[i])
        current_vals = trajectories[i - 1, :]
        assigned = np.zeros(len(new_eigs), dtype=bool)

        for j in range(n_tracks):
            if np.isnan(current_vals[j]):
                continue
            dists = np.abs(new_eigs - current_vals[j])
            dists[assigned] = np.inf
            best = np.argmin(dists)
            if dists[best] < threshold:
                trajectories[i, j] = new_eigs[best]
                assigned[best] = True

        for k in range(len(new_eigs)):
            if not assigned[k]:
                new_col = np.full(n_L, np.nan)
                new_col[i] = new_eigs[k]
                trajectories = np.column_stack([trajectories, new_col])
                n_tracks += 1

    return trajectories


def find_resonance(L_arr, trajectories, mc2):
    n_L = len(L_arr)
    if trajectories.shape[1] == 0:
        print("WARNING: No tracks found — trajectories matrix is empty.")
        return (None, None, None)

    coverage = np.sum(~np.isnan(trajectories), axis=0) / n_L
    good = np.where(coverage >= 0.8)[0]

    if len(good) == 0:
        print("WARNING: No tracks pass 80% coverage filter. No resonance found.")
        return (None, None, None)

    i_start = n_L // 5
    i_end = 4 * n_L // 5

    best_score = np.inf
    best_idx = None

    for j in good:
        col = trajectories[:, j].copy()
        nans = np.isnan(col)
        if np.all(nans):
            continue
        xs = np.where(~nans)[0]
        col_interp = np.interp(np.arange(n_L), xs, col[xs])
        dE_dL = np.gradient(col_interp, L_arr)
        central_dEdL = np.abs(dE_dL[i_start:i_end])
        score = np.var(central_dEdL)
        if score < best_score:
            best_score = score
            best_idx = j

    if best_idx is None:
        print("WARNING: Could not select resonance track.")
        return (None, None, None)

    col = trajectories[:, best_idx]
    central_vals = col[i_start:i_end]
    valid = ~np.isnan(central_vals)
    E_res = np.mean(central_vals[valid])

    nans = np.isnan(col)
    xs = np.where(~nans)[0]
    col_interp = np.interp(np.arange(n_L), xs, col[xs])
    dE_dL = np.gradient(col_interp, L_arr)
    central_abs_dEdL = np.abs(dE_dL[i_start:i_end])
    plateau_local_idx = np.argmin(central_abs_dEdL)
    plateau_global_idx = i_start + plateau_local_idx
    L_opt = L_arr[plateau_global_idx]

    return (E_res, L_opt, best_idx)
