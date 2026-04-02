from __future__ import annotations

import argparse
import importlib
import math
import os
from typing import Callable, cast

import numpy as np
from numpy.typing import NDArray

_config = importlib.import_module("config")
_mabgps_ccr = importlib.import_module("mabgps_ccr")

Z: int = int(cast(int, getattr(_config, "Z")))
KAPPA: int = int(cast(int, getattr(_config, "KAPPA")))
LAMBDA_SHIELD: float = float(cast(float, getattr(_config, "LAMBDA_SHIELD")))
C_LIGHT: float = float(cast(float, getattr(_config, "C_LIGHT")))
M_ELECTRON: float = float(cast(float, getattr(_config, "M_ELECTRON")))
L_SCALE: float = float(cast(float, getattr(_config, "L_SCALE")))
ALPHA_MAP: float = float(cast(float, getattr(_config, "ALPHA_MAP")))
N_POINTS: int = int(cast(int, getattr(_config, "N_POINTS")))

SolverFn = Callable[..., tuple[NDArray[np.complex128], object, object]]
solve_mabgps_ccr: SolverFn = cast(SolverFn, getattr(_mabgps_ccr, "solve_mabgps_ccr"))


def make_theta_grid(
    theta_start: float, theta_stop: float, theta_step: float
) -> NDArray[np.float64]:
    if theta_step <= 0:
        raise ValueError("theta_step must be > 0")
    if theta_stop < theta_start:
        raise ValueError("theta_stop must be >= theta_start")

    n = int(math.floor((theta_stop - theta_start) / theta_step + 1e-12)) + 1
    thetas = np.asarray(
        [theta_start + theta_step * k for k in range(n)],
        dtype=np.float64,
    )
    last = float(cast(np.float64, thetas[-1])) if thetas.size else float(theta_start)
    if thetas.size and abs(last - theta_stop) <= 10 * np.finfo(np.float64).eps * max(
        1.0, abs(theta_stop)
    ):
        thetas[-1] = float(theta_stop)
    return thetas.astype(np.float64)


def expected_eig_count(N: int) -> int:
    return 2 * (int(N) - 2)


def run_scan(
    thetas: NDArray[np.float64],
    N: int,
    L: float,
    alpha_map: float,
    *,
    solver: SolverFn = solve_mabgps_ccr,
    params_from_config: bool = True,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    thetas = np.asarray(thetas, dtype=np.float64)
    n_theta = int(thetas.size)
    n_eig_expected = expected_eig_count(N)

    E_re = np.full((n_theta, n_eig_expected), np.nan, dtype=np.float64)
    E_im = np.full((n_theta, n_eig_expected), np.nan, dtype=np.float64)

    if params_from_config:
        Z_ = Z
        kappa_ = KAPPA
        lambda_shield_ = LAMBDA_SHIELD
        c_ = C_LIGHT
    else:
        raise ValueError("params_from_config=False is not supported in this CLI")

    for i in range(n_theta):
        theta = float(cast(np.float64, thetas[i]))
        try:
            E_complex, _vecs, _r = solver(
                N=N,
                L=L,
                alpha_map=alpha_map,
                Z=Z_,
                lambda_shield=lambda_shield_,
                kappa=kappa_,
                c=c_,
                theta=float(theta),
                return_complex=True,
            )
        except Exception as e:
            print(f"WARNING: theta={theta} solver failed: {e}")
            continue

        E_complex = np.asarray(E_complex)
        n_take = min(n_eig_expected, int(E_complex.size))

        re = np.real(E_complex[:n_take]).astype(np.float64, copy=False)
        im = np.imag(E_complex[:n_take]).astype(np.float64, copy=False)

        bad = ~np.isfinite(re) | ~np.isfinite(im)
        if np.any(bad):
            bad_count = int(np.sum(bad))
            print(
                f"WARNING: theta={theta} has {bad_count} NaN/Inf eigenvalues; setting to NaN"
            )
            re = re.copy()
            im = im.copy()
            re[bad] = np.nan
            im[bad] = np.nan

        E_re[i, :n_take] = re
        E_im[i, :n_take] = im

        if E_complex.size != n_eig_expected:
            print(
                f"WARNING: theta={theta} eigenvalue count {E_complex.size} != expected {n_eig_expected}; "
                + f"stored first {n_take}"
            )

    return E_re, E_im


def save_npz(
    out_path: str,
    E_re: NDArray[np.float64],
    E_im: NDArray[np.float64],
    thetas: NDArray[np.float64],
    metadata_dict: dict[str, float | int],
) -> None:
    payload: dict[str, NDArray[np.float64]] = {
        "E_re": np.asarray(E_re, dtype=np.float64),
        "E_im": np.asarray(E_im, dtype=np.float64),
        "thetas": np.asarray(thetas, dtype=np.float64),
    }

    for k, v in metadata_dict.items():
        payload[k] = np.asarray(v, dtype=np.float64)

    np.savez(out_path, **payload)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CCR theta scan data acquisition")
    _ = p.add_argument("--theta-start", type=float, required=True)
    _ = p.add_argument("--theta-stop", type=float, required=True)
    _ = p.add_argument("--theta-step", type=float, required=True)
    _ = p.add_argument("--out", type=str, required=True, help="Output .npz path")
    _ = p.add_argument("--N", type=int, default=N_POINTS)
    _ = p.add_argument("--L", type=float, default=L_SCALE)
    _ = p.add_argument("--alpha-map", type=float, default=ALPHA_MAP)

    args = p.parse_args(argv)

    theta_start = float(cast(float, args.theta_start))
    theta_stop = float(cast(float, args.theta_stop))
    theta_step = float(cast(float, args.theta_step))
    out_path = str(cast(str, args.out))
    N = int(cast(int, args.N))
    L = float(cast(float, args.L))
    alpha_map = float(cast(float, args.alpha_map))

    out_dir = os.path.dirname(out_path) or "."
    if not os.path.isdir(out_dir):
        raise FileNotFoundError(f"Output directory does not exist: {out_dir}")

    thetas = make_theta_grid(theta_start, theta_stop, theta_step)
    E_re, E_im = run_scan(
        thetas,
        N=N,
        L=L,
        alpha_map=alpha_map,
        solver=solve_mabgps_ccr,
        params_from_config=True,
    )

    mc2 = float(M_ELECTRON * (C_LIGHT**2))
    meta = {
        "mc2": mc2,
        "meta_Z": float(Z),
        "meta_kappa": float(KAPPA),
        "meta_lambda": float(LAMBDA_SHIELD),
        "meta_N": float(N),
        "meta_L": float(L),
        "meta_alpha": float(alpha_map),
        "meta_c": float(C_LIGHT),
    }

    save_npz(out_path, E_re, E_im, thetas, meta)

    n_theta = int(thetas.size)
    n_eig = expected_eig_count(N)
    total_points = n_theta * n_eig
    nan_mask: NDArray[np.bool_] = cast(
        NDArray[np.bool_], np.all(np.isnan(E_re), axis=1)
    )
    nan_rows = int(np.count_nonzero(nan_mask))

    print(
        f"Scan complete: n_theta={n_theta}, n_eig={n_eig}, total_points={total_points}, nan_rows={nan_rows}"
    )
    print(
        f"Saved -> {out_path}  (Z={Z}, kappa={KAPPA}, lambda={LAMBDA_SHIELD:.2f}, N={N}, L={L}, alpha={alpha_map})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
