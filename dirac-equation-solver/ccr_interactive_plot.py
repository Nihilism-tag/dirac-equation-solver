"""
ccr_interactive_plot.py — Interactive complex-energy scatter plot for CCR theta scan data.

Usage:
    python ccr_interactive_plot.py --in ccr_data.npz
    MPLBACKEND=Agg python ccr_interactive_plot.py --in /tmp/ccr_smoke.npz --no-show --out /tmp/ccr_plot.png

Controls:
    toolbar zoom:   drag rectangle with zoom-to-rectangle toolbar button
    z:              toggle RectangleSelector box-zoom (draw rectangle to zoom)
    r:              reset to original/initial view limits
    s:              save current zoomed view (timestamped PNG, or --out path)

Keys are active when the plot window has focus.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.collections import PathCollection
    from matplotlib.figure import Figure


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Interactive CCR complex-energy scatter plot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--in",
        dest="input",
        required=True,
        metavar="PATH",
        help="Input .npz file from ccr_scan.py",
    )
    p.add_argument(
        "--out",
        type=str,
        default=None,
        metavar="PATH",
        help="Save figure to this path (PNG/PDF/SVG)",
    )
    p.add_argument(
        "--no-show",
        dest="no_show",
        action="store_true",
        help="Do not call plt.show() (useful for headless/CI)",
    )
    p.add_argument(
        "--re-min",
        type=float,
        default=None,
        metavar="FLOAT",
        help="Initial x-axis lower limit (Re(E)/mc²)",
    )
    p.add_argument(
        "--re-max",
        type=float,
        default=None,
        metavar="FLOAT",
        help="Initial x-axis upper limit (Re(E)/mc²)",
    )
    p.add_argument(
        "--im-min",
        type=float,
        default=None,
        metavar="FLOAT",
        help="Initial y-axis lower limit (Im(E)/mc²)",
    )
    p.add_argument(
        "--im-max",
        type=float,
        default=None,
        metavar="FLOAT",
        help="Initial y-axis upper limit (Im(E)/mc²)",
    )
    p.add_argument(
        "--cmap",
        type=str,
        default="turbo",
        metavar="NAME",
        help="Matplotlib colormap name for theta (default: turbo)",
    )
    p.add_argument(
        "--s",
        type=float,
        default=3.0,
        metavar="FLOAT",
        help="Scatter marker size in points² (default: 3)",
    )
    p.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        metavar="FLOAT",
        help="Scatter marker alpha (default: 0.5)",
    )
    return p.parse_args(argv)


def load_data(
    path: str,
) -> tuple[
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
    float,
]:
    """Load .npz produced by ccr_scan.py.

    Returns
    -------
    re_flat    : 1-D float64 array of Re(E)/mc², length n_theta*n_eig
    im_flat    : 1-D float64 array of Im(E)/mc², same length
    theta_flat : 1-D float64 array of theta values repeated n_eig times each
    mc2        : scalar rest-mass energy used for normalisation
    """
    data = np.load(path)
    E_re = np.asarray(data["E_re"], dtype=np.float64)
    E_im = np.asarray(data["E_im"], dtype=np.float64)
    thetas = np.asarray(data["thetas"], dtype=np.float64)
    mc2 = float(data["mc2"])

    _n_theta, n_eig = E_re.shape

    re_flat: npt.NDArray[np.float64] = (E_re / mc2).ravel()
    im_flat: npt.NDArray[np.float64] = (E_im / mc2).ravel()
    theta_flat: npt.NDArray[np.float64] = np.repeat(thetas, n_eig)

    return re_flat, im_flat, theta_flat, mc2


def _resolve_save_path(
    input_path: str,
    out_arg: str | None,
    now_dt: datetime | None = None,
) -> Path:
    """Resolve the output path for a keypress-triggered save.

    Rules
    -----
    - If *out_arg* is provided, return ``Path(out_arg)`` exactly.
    - Otherwise generate a timestamped filename in the same directory as
      *input_path*: ``<input_dir>/ccr_zoomed_YYYYMMDD_HHMMSS.png``

    Parameters
    ----------
    input_path : str
        Path to the ``.npz`` input file (absolute or relative).
    out_arg : str | None
        Value of ``--out`` CLI argument; ``None`` if not provided.
    now_dt : datetime | None
        Datetime to use for the timestamp.  Defaults to ``datetime.now()``.
        Pass an explicit value in tests for deterministic output.
    """
    if out_arg is not None:
        return Path(out_arg)
    ts = (now_dt or datetime.now()).strftime("%Y%m%d_%H%M%S")
    parent = Path(input_path).parent
    return parent / f"ccr_zoomed_{ts}.png"


def build_figure(
    re_flat: npt.NDArray[np.float64],
    im_flat: npt.NDArray[np.float64],
    theta_flat: npt.NDArray[np.float64],
    *,
    re_min: float | None = None,
    re_max: float | None = None,
    im_min: float | None = None,
    im_max: float | None = None,
    cmap: str = "turbo",
    s: float = 3.0,
    alpha: float = 0.5,
) -> tuple[Figure, Axes, PathCollection]:
    """Create and return (fig, ax, scatter) with colorbar, reference lines, and usage hint.

    Interactive callbacks are NOT attached here; call ``attach_callbacks`` separately.
    This separation allows headless rendering without binding any GUI event loop.
    """
    import matplotlib.pyplot as plt
    from matplotlib.axes import Axes as _Axes
    from matplotlib.figure import Figure as _Figure
    from typing import cast as _cast

    # --- Dark theme + keybinding tweaks (local to this call) ---
    _dark_bg = "#0d1117"
    _dark_axes = "#161b22"
    _dark_edge = "#444c56"
    _fg = "#cdd9e5"
    plt.rcParams.update(
        {
            "figure.facecolor": _dark_bg,
            "axes.facecolor": _dark_axes,
            "axes.edgecolor": _dark_edge,
            "axes.labelcolor": _fg,
            "xtick.color": _fg,
            "ytick.color": _fg,
            "text.color": _fg,
            "grid.color": "#2d333b",
            "savefig.facecolor": _dark_bg,
            "savefig.edgecolor": _dark_bg,
            "keymap.save": [],
        }
    )

    fig_raw, ax_raw = plt.subplots(figsize=(10, 7))
    fig = _cast(_Figure, fig_raw)
    ax = _cast(_Axes, ax_raw)

    theta_min = float(np.nanmin(theta_flat))
    theta_max = float(np.nanmax(theta_flat))

    sc = ax.scatter(
        re_flat,
        im_flat,
        c=theta_flat,
        cmap=cmap,
        vmin=theta_min,
        vmax=theta_max,
        s=s,
        alpha=alpha,
        linewidths=0,
        rasterized=True,
    )

    cbar = fig.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("θ (rad)", fontsize=11, color=_fg)
    cbar.ax.yaxis.set_tick_params(color=_fg)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=_fg)

    ax.axvline(x=1.0, color="#6e7681", linestyle="--", linewidth=0.8, label="Re(E)=mc²")
    ax.axhline(y=0.0, color="#adbac7", linestyle="-", linewidth=0.8, label="Im(E)=0")

    ax.set_xlabel("Re(E) / mc²", fontsize=12)
    ax.set_ylabel("Im(E) / mc²", fontsize=12)
    ax.set_title("CCR complex eigenvalue spectrum", fontsize=13)

    if re_min is not None or re_max is not None:
        cur_xl = ax.get_xlim()
        ax.set_xlim(
            re_min if re_min is not None else cur_xl[0],
            re_max if re_max is not None else cur_xl[1],
        )
    if im_min is not None or im_max is not None:
        cur_yl = ax.get_ylim()
        ax.set_ylim(
            im_min if im_min is not None else cur_yl[0],
            im_max if im_max is not None else cur_yl[1],
        )

    ax.text(
        0.99,
        0.02,
        "toolbar zoom: drag | z: RectSelector | r: reset | s: save",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        color="gray",
        alpha=0.75,
    )

    fig.tight_layout()
    return fig, ax, sc  # type: ignore[return-value]


def attach_callbacks(
    fig: Figure,
    ax: Axes,
    sc: PathCollection,
    re_flat: npt.NDArray[np.float64],
    im_flat: npt.NDArray[np.float64],
    theta_flat: npt.NDArray[np.float64],
    *,
    out_arg: str | None = None,
    input_path: str = "",
) -> None:
    """Attach hover annotation and keyboard zoom/reset callbacks to an interactive figure."""
    from matplotlib.backend_bases import MouseButton
    from matplotlib.widgets import RectangleSelector

    orig_xlim = ax.get_xlim()
    orig_ylim = ax.get_ylim()

    annot = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(10, 10),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.3", fc="#1c2128", alpha=0.92, ec="#444c56"),
        fontsize=8,
        color="#cdd9e5",
        visible=False,
    )

    def _on_hover(event: Any) -> None:
        if event.inaxes != ax:
            annot.set_visible(False)
            fig.canvas.draw_idle()
            return

        cont, ind = sc.contains(event)
        if cont:
            idx = ind["ind"][0]
            re_val = float(re_flat[idx])
            im_val = float(im_flat[idx])
            th_val = float(theta_flat[idx])
            annot.xy = (re_val, im_val)
            annot.set_text(
                f"Re/mc²={re_val:.5g}\nIm/mc²={im_val:.5g}\nθ={th_val:.4g} rad"
            )
            annot.set_visible(True)
        else:
            annot.set_visible(False)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", _on_hover)

    rect_selector_state: dict[str, bool] = {"active": False}

    def _on_rect_select(eclick: Any, erelease: Any) -> None:
        if None in (eclick.xdata, erelease.xdata, eclick.ydata, erelease.ydata):
            return
        x1, x2 = sorted([eclick.xdata, erelease.xdata])
        y1, y2 = sorted([eclick.ydata, erelease.ydata])
        if abs(x2 - x1) > 1e-12 and abs(y2 - y1) > 1e-12:
            ax.set_xlim(x1, x2)
            ax.set_ylim(y1, y2)
            fig.canvas.draw_idle()

    rs = RectangleSelector(
        ax,
        _on_rect_select,
        useblit=True,
        button=MouseButton.LEFT,  # pyright: ignore[reportArgumentType]
        minspanx=5,
        minspany=5,
        spancoords="pixels",
        interactive=False,
    )
    rs.set_active(False)

    def _on_key_press(event: Any) -> None:
        if event.key == "z":
            new_state = not rect_selector_state["active"]
            rect_selector_state["active"] = new_state
            rs.set_active(new_state)
            print(
                f"[ccr_interactive_plot] RectangleSelector {'ON' if new_state else 'OFF'}"
            )
            fig.canvas.draw_idle()
        elif event.key == "r":
            ax.set_xlim(orig_xlim)
            ax.set_ylim(orig_ylim)
            fig.canvas.draw_idle()
        elif event.key == "s":
            save_path = _resolve_save_path(input_path, out_arg)
            out_dir = save_path.parent
            if not out_dir.exists():
                print(
                    f"[ccr_interactive_plot] Save failed: directory does not exist:"
                    f" {out_dir}"
                )
                return
            fig.savefig(
                save_path,
                dpi=150,
                bbox_inches="tight",
                pad_inches=0.08,
                facecolor=fig.get_facecolor(),
                edgecolor="none",
            )
            print(f"[ccr_interactive_plot] Saved zoomed view -> {save_path}")

    fig.canvas.mpl_connect("key_press_event", _on_key_press)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.no_show:
        import matplotlib

        current_backend = matplotlib.get_backend()
        interactive_backends = {
            "TkAgg",
            "Qt5Agg",
            "Qt4Agg",
            "GTK3Agg",
            "WXAgg",
            "MacOSX",
            "macosx",
        }
        if (
            current_backend in interactive_backends
            or "agg" not in current_backend.lower()
        ):
            matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    re_flat, im_flat, theta_flat, mc2 = load_data(args.input)

    fig, ax, sc = build_figure(
        re_flat,
        im_flat,
        theta_flat,
        re_min=args.re_min,
        re_max=args.re_max,
        im_min=args.im_min,
        im_max=args.im_max,
        cmap=args.cmap,
        s=args.s,
        alpha=args.alpha,
    )

    if not args.no_show:
        attach_callbacks(
            fig,
            ax,
            sc,
            re_flat,
            im_flat,
            theta_flat,
            out_arg=args.out,
            input_path=args.input,
        )

    if args.out:
        fig.savefig(args.out, dpi=150, bbox_inches="tight")
        print(f"[ccr_interactive_plot] Saved -> {args.out}")

    if not args.no_show:
        plt.show()

    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
