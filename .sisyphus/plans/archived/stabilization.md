# Stabilization Method: Resonance State Search & Visualization

## TL;DR

> **Quick Summary**: Fix a critical wavefunction oscillation bug in the Dirac solver (`mabgps.py`), then implement a 3-phase stabilization workflow to locate resonance states in the positive continuum and produce two publication-quality figures.
>
> **Deliverables**:
> - `mabgps.py` *(modified)* — remove forced symmetrization, restore `eig`+`.real` solver
> - `test_solvers.py` *(modified)* — add wavefunction smoothness assertion
> - `stab_scan.py` *(new)* — L-scale scan + level tracking + plateau detection
> - `stab_plot.py` *(new)* — stabilization graph + resonance wavefunction/potential figure
> - `run_stab.py` *(new)* — entry point producing `fig_stabilization.png` + `fig_resonance_wf.png`
> - `test_stabilization.py` *(new)* — fast unit + smoke tests
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: Task 0 → Task 1 → Task 3 → Task 4 → F1-F3

---

## Context

### H_issue.md Discovery (Integrated)
A **new bug** was discovered and documented in `H_issue.md` after the mabgps-fix plan:

> **Bug**: The forced symmetrization `H = 0.5*(H+H.T)` in `mabgps.py` causes "Odd-Even Decoupling" — the wavefunction shows extreme Nyquist-mode sawtooth oscillations instead of smooth exponential decay.
>
> **Root Cause**: Symmetrizing the Chebyshev derivative matrix degrades the global spectral operator into a local central-difference-like operator. Central differences evaluate the derivative of a Nyquist mode (`+1,-1,+1,-1...`) as exactly zero — creating a "zero-kinetic-energy trap" that the eigensolver exploits.
>
> **Fix** (from `H_issue.md`): (1) Remove `H = 0.5*(H+H.T)`, (2) Use `scipy.linalg.eig(H)`, (3) Extract `eigenvalues = eigenvalues_complex.real` — imaginary parts are numerical noise at ~1e-14, no threshold filtering needed.

This fix is **prerequisite** to stabilization (Phase 3 requires smooth eigenvectors). It is **Task 0** (Wave 0, blocks all other tasks).

### Original Request
User provided `stabalization_plan.md` describing a 3-phase plan:
1. **Data Acquisition**: Scan L_scale ∈ [0.5, 3.0] step 0.05, collect eigenvalues in 0.9mc² < E < 1.2mc²
2. **Automated Identification**: Compute dE/dL, find flattest plateau → resonance energy E_res, optimal L_opt
3. **Core Visualization**: (a) Stabilization graph — gray pseudo-continuum lines + thick red resonance plateau; (b) Resonance wavefunction + V_eff with shaded inner pocket

### Metis Review
**Identified Gaps** (addressed below):
- No-resonance-found contract → function returns `(None, None, None)` with printed warning; plots show empty frame with message
- Variable eigenvalue count per L step → `track_levels` uses NaN filling + 80% coverage filter
- Matplotlib headless → all plot functions call `matplotlib.use('Agg')` guard or accept `fig` injection
- V_eff near r=0 singularity → mask first 5 grid points from V_eff visualization
- Fast test mode → test functions call solver with `N=50, L_min=1.0, L_max=1.2, L_step=0.1`

### Interview Decisions
- **Output format**: PNG, 150 dpi, saved to cwd (consistent with existing `spectrum.png`, `wavefunction.png`)
- **Single resonance**: Return the single best plateau (minimum variance of dE/dL)
- **Greedy level tracking**: Nearest-neighbor matching; document that avoided crossings may cause identity swaps
- **V_eff formula**: Non-relativistic visualization proxy — `V_eff(r) = [V(r) + κ(κ+1)/(2r²)] / mc²`
- **Energy window**: Absolute total energy including rest mass (consistent with existing code convention)

---

## Work Objectives

### Core Objective
(1) Fix the Odd-Even Decoupling bug in `mabgps.py` per `H_issue.md`. (2) Implement the stabilization method as a self-contained module set that calls the fixed `solve_mabgps()` and produces two academic figures demonstrating resonance state identification.

### Concrete Deliverables
- `mabgps.py` *(modified)* — remove `H = 0.5*(H+H.T)` and `eigh`; use `eig`+`.real`
- `test_solvers.py` *(modified)* — add wavefunction smoothness test (no Nyquist oscillation)
- `stab_scan.py` *(new)* — `scan_stabilization()`, `track_levels()`, `find_resonance()`
- `stab_plot.py` *(new)* — `plot_stabilization_graph()`, `plot_resonance_wavefunction()`
- `run_stab.py` *(new)* — entry point
- `test_stabilization.py` *(new)* — unit tests (synthetic) + smoke test (real solver, small N)
- `fig_stabilization.png` — stabilization graph
- `fig_resonance_wf.png` — resonance wavefunction + V_eff figure

### Definition of Done
- [x] `pytest test_solvers.py -q` — all 6 existing tests + new smoothness test PASS
- [x] `python run_stab.py` exits with code 0
- [x] `fig_stabilization.png` and `fig_resonance_wf.png` exist and are > 20 KB
- [x] `pytest test_stabilization.py -q` completes in < 60 seconds with 0 failures

### Must Have
- `mabgps.py`: symmetrization line REMOVED; `eig`+`.real` used; eigenvalue count still `2*(N-2)`
- `scan_stabilization()` accepts `L_min`, `L_max`, `L_step`, `E_min_frac`, `E_max_frac` with config defaults
- `find_resonance()` returns `(None, None, None)` gracefully when no plateau found
- All plot functions work under `matplotlib.use('Agg')` (headless)

### Must NOT Have (Guardrails)
- Must NOT modify: `config.py`, `potential.py`, `bspline.py`, `main.py`, `plot.py`
- `mabgps.py`: ONLY the two targeted changes (remove symmetrization line + swap `eigh` → `eig`+`.real`); no other logic changes
- `test_solvers.py`: ONLY add the smoothness test; existing 6 tests must remain PASSING
- No new heavy dependencies beyond `numpy`, `matplotlib`, `scipy` (already used)
- No CLI argparse interface (out of scope)
- No parallelization, caching, or progress bars
- No multiple-resonance catalog or multi-κ/Z sweeps
- No hardcoded energy values — always derive from `mc2 = M_ELECTRON * C_LIGHT**2`
- Do NOT re-introduce imaginary threshold filtering (`|Im| < 1e-8`) — use `.real` only

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES (`pytest`, `test_solvers.py`)
- **Automated tests**: YES (Tests-after)
- **Framework**: pytest (consistent with existing)

### QA Policy
- Unit tests use **synthetic data** (no real solver) for `track_levels` and `find_resonance`
- Smoke test uses **real solver** with `N=50, L_min=1.0, L_max=1.2, L_step=0.1` for speed
- Plot tests assert file existence + file size > 20 KB
- All QA scenarios run under `matplotlib.use('Agg')`

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 0 (MUST RUN FIRST — sequential, bug fix prerequisite):
└── Task 0: mabgps.py + test_solvers.py — fix Odd-Even Decoupling [quick]

Wave 1 (After Task 0 — independent new modules, parallel):
├── Task 1: stab_scan.py — scan + track + detect [unspecified-high]
└── Task 2: stab_plot.py — two plot functions [visual-engineering]

Wave 2 (After Wave 1 — integration):
├── Task 3: run_stab.py — entry point [quick]
└── Task 4: test_stabilization.py — tests [unspecified-high]

Wave FINAL (After ALL tasks — parallel reviews):
├── F1: Physics correctness audit [oracle]
├── F2: Code quality review [unspecified-high]
└── F3: Scope fidelity check [deep]
→ Present consolidated results → Get explicit user okay
```

### Dependency Matrix

| Task | Blocked By | Blocks |
|------|-----------|--------|
| 0 | — (start immediately) | 1, 2, 3, 4, F1-F3 |
| 1 | 0 | 3, 4, F1-F3 |
| 2 | 0 | 3, 4, F1-F3 |
| 3 | 1, 2 | F1-F3 |
| 4 | 1, 2 | F1-F3 |
| F1-F3 | 0, 1, 2, 3, 4 | — |

---

## TODOs

---

- [x] 0. Fix `mabgps.py` + `test_solvers.py` — Odd-Even Decoupling (prerequisite)

  **What to do**:

  This task implements the fix described in `H_issue.md`. Modify two existing files with **surgical changes only**.

  **Change 1 — `mabgps.py`** (2 lines changed, nothing else):

  Delete `H = 0.5 * (H + H.T)` entirely (the line after the `np.block` call). Then replace:
  ```python
  eigenvalues, eigenvectors = linalg.eigh(H)
  ```
  with:
  ```python
  eigenvalues_complex, eigenvectors = linalg.eig(H)
  eigenvalues = eigenvalues_complex.real
  ```
  The sort/return block remains completely unchanged. No other changes to `mabgps.py`.

  **Change 2 — `test_solvers.py`** (add 1 test method to `TestMABGPS` class):

  Append this method to the `TestMABGPS` class (after `test_mabgps_validation_lambda0`):
  ```python
  def test_mabgps_wavefunction_smooth(self):
      """Ground state wavefunction must be smooth (no Nyquist sawtooth oscillation)."""
      E, vecs, r = solve_mabgps()
      mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2

      bound_mask = (E > 0) & (E < mc2)
      assert np.any(bound_mask), "No bound states found"
      ground_idx = np.where(bound_mask)[0][np.argmin(E[bound_mask])]
      N2 = len(r)
      P = vecs[:N2, ground_idx].real

      # Nyquist oscillation: sign alternates every point → rate ≈ 1.0
      # Smooth wavefunction: few sign changes → rate ≪ 0.5
      signs = np.sign(np.diff(P))
      sign_changes = np.sum(signs[:-1] != signs[1:])
      oscillation_rate = sign_changes / len(signs)
      assert oscillation_rate < 0.5, (
          f"Nyquist oscillation detected: sign-change rate = {oscillation_rate:.3f}"
      )
  ```

  **Must NOT do**:
  - Do NOT modify `config.py`, `potential.py`, `bspline.py`, `main.py`, `plot.py`
  - Do NOT change the signature or return values of `solve_mabgps()`
  - Do NOT re-introduce `|Im| < threshold` filtering — use `.real` ONLY
  - Do NOT touch any other line in `mabgps.py` beyond the two targeted changes
  - Do NOT comment out `H = 0.5*(H+H.T)` — DELETE it entirely

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Surgical 2-line change + add 1 test method; fully specified with exact code
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (Wave 0 — must complete before all other tasks)
  - **Blocks**: Tasks 1, 2, 3, 4, F1, F2, F3
  - **Blocked By**: None (start immediately)

  **References**:

  **Pattern References**:
  - `mabgps.py:142-155` — The exact target block: `H = np.block(...)`, then `H = 0.5*(H+H.T)`, then `eigenvalues, eigenvectors = linalg.eigh(H)` — modify lines 149 and 151
  - `mabgps.py:13-14` — `from scipy import linalg` already imported; `linalg.eig` is available
  - `test_solvers.py:34-55` — `TestMABGPS` class — add new method after line 55
  - `H_issue.md:23-26` — Verbatim fix specification

  **Acceptance Criteria**:
  - [x] `python -c "from mabgps import solve_mabgps; import config as cfg; E,_,_=solve_mabgps(); assert len(E)==2*(cfg.N_POINTS-2); print('eigencount OK')"` → prints `eigencount OK`
  - [x] `pytest test_solvers.py -q` → **7 passed**, 0 failed (6 original + 1 new smoothness)
  - [x] Smoothness check: oscillation_rate < 0.5 on ground state wavefunction

  **QA Scenarios**:

  ```
  Scenario: solve_mabgps preserves eigenvalue count after fix
    Tool: Bash (python -c)
    Steps:
      1. python -c "from mabgps import solve_mabgps; import config as cfg; E,_,_=solve_mabgps(); assert len(E)==2*(cfg.N_POINTS-2), f'Got {len(E)}'; print('PASS')"
    Expected Result: prints PASS
    Evidence: .sisyphus/evidence/stab-task0-eigencount.txt

  Scenario: Ground state wavefunction is smooth (no Nyquist oscillation)
    Tool: Bash (python -c)
    Steps:
      1. python -c "
  import numpy as np
  from mabgps import solve_mabgps
  import config as cfg
  E, vecs, r = solve_mabgps()
  mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
  bound = (E > 0) & (E < mc2)
  gi = np.where(bound)[0][np.argmin(E[bound])]
  P = vecs[:len(r), gi].real
  signs = np.sign(np.diff(P))
  rate = np.sum(signs[:-1] != signs[1:]) / len(signs)
  assert rate < 0.5, f'Nyquist: rate={rate:.3f}'
  print(f'oscillation_rate={rate:.3f} PASS')
  "
    Expected Result: "oscillation_rate=X.XXX PASS" with X.XXX < 0.5
    Evidence: .sisyphus/evidence/stab-task0-smoothness.txt

  Scenario: All test_solvers.py tests pass after fix
    Tool: Bash (pytest)
    Steps:
      1. pytest test_solvers.py -q --tb=short
    Expected Result: "7 passed in X.XXs"
    Evidence: .sisyphus/evidence/stab-task0-pytest.txt
  ```

  **Evidence to Capture**:
  - [x] `stab-task0-eigencount.txt`
  - [x] `stab-task0-smoothness.txt`
  - [x] `stab-task0-pytest.txt`

  **Commit**: YES (standalone)
  - Message: `fix(mabgps): remove H symmetrization, restore eig+.real to fix Odd-Even Decoupling`
  - Files: `mabgps.py`, `test_solvers.py`
  - Pre-commit: `pytest test_solvers.py -q`

---

- [x] 1. `stab_scan.py` — L-scan, level tracking, resonance finder

  **What to do**:

  Implement three functions in a new file `stab_scan.py`:

  **Function 1: `scan_stabilization()`**
  ```python
  def scan_stabilization(
      L_min=0.5, L_max=3.0, L_step=0.05,
      E_min_frac=0.9, E_max_frac=1.2,
      N=N_POINTS, alpha_map=ALPHA_MAP,
      Z=Z, lambda_shield=LAMBDA_SHIELD, kappa=KAPPA, c=C_LIGHT
  ) -> dict:
  ```
  - Compute `mc2 = M_ELECTRON * c**2`
  - Build `L_arr = np.arange(L_min, L_max + L_step/2, L_step)`
  - For each L in L_arr: call `solve_mabgps(N=N, L=L, alpha_map=alpha_map, Z=Z, lambda_shield=lambda_shield, kappa=kappa, c=c)`, extract eigenvalues `E` in window `[E_min_frac * mc2, E_max_frac * mc2]`
  - Return dict: `{'L_arr': L_arr, 'eigenvalue_sets': list_of_arrays, 'mc2': mc2}`
  - Print progress: `print(f"  L={L:.3f}: {len(E_win)} levels in window")` every 10 steps

  **Function 2: `track_levels(scan_result) -> np.ndarray`**
  - Input: scan_result dict
  - Algorithm: greedy nearest-neighbor matching across adjacent L steps
    - `n_L = len(L_arr)`; start with first non-empty L step, initialize tracks with sorted eigenvalues
    - For each subsequent L step: for each new eigenvalue, find nearest unassigned existing track (by energy distance); assign if distance < threshold (use `0.5 * mc2 * L_step`); unassigned new eigenvalues start new tracks; unmatched tracks get NaN
    - Fill result matrix `trajectories` of shape `(n_L, n_tracks)` with NaN padding
  - Return: `trajectories` array

  **Function 3: `find_resonance(L_arr, trajectories, mc2) -> tuple`**
  - Filter trajectories with >= 80% non-NaN coverage
  - Compute `dE_dL[i, :]` using `np.gradient(trajectories[:, i], L_arr)` for each track i, ignoring NaN via interpolation
  - Score each track: `variance of |dE_dL|` over central 60% of L range (indices `n_L//5 : 4*n_L//5`)
  - Resonance = track with minimum score
  - `E_res` = mean of that track's values in the central 60% range
  - `L_opt` = L value closest to center of plateau (argmin |dE_dL| in central range)
  - If no tracks pass coverage filter: return `(None, None, None)` and print warning
  - Return: `(E_res, L_opt, res_idx)` where res_idx is column index in trajectories

  **Must NOT do**:
  - Do NOT modify config.py — import constants only (`from config import N_POINTS, ALPHA_MAP, Z, LAMBDA_SHIELD, KAPPA, C_LIGHT, M_ELECTRON`)
  - Do NOT use `from mabgps import *` — import only `solve_mabgps`
  - Do NOT implement overlap-based eigenvector tracking (out of scope)
  - Do NOT add parallelization or caching

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Numerical algorithm implementation requiring careful handling of NaN, variable-length arrays, and finite-difference derivatives; not pure physics/visual but substantial computational logic
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `playwright`: No UI interaction needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Tasks 3, 4, F1, F2, F3
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `mabgps.py:83-157` — `solve_mabgps()` signature: accepts `N, L, alpha_map, Z, lambda_shield, kappa, c` as keyword args; returns `(E_sorted, vecs_sorted, r_interior)`
  - `config.py:1-25` — All importable constants: `N_POINTS, ALPHA_MAP, Z, LAMBDA_SHIELD, KAPPA, C_LIGHT, M_ELECTRON`
  - `main.py:34` — Pattern for overriding `lambda_shield=0.0` while keeping other defaults: `solve_mabgps(lambda_shield=0.0)`

  **API/Type References**:
  - `solve_mabgps()` returns `E_sorted` (real float64 array, 2*(N-2) elements), sorted ascending
  - Energy convention: TOTAL energy including rest mass; bound states satisfy `0 < E < mc2`
  - `mc2 = M_ELECTRON * C_LIGHT**2` ≈ 18779 a.u. for `C_LIGHT=137.036, M_ELECTRON=1.0`

  **Acceptance Criteria**:

  - [x] `python -c "from stab_scan import scan_stabilization; r = scan_stabilization(L_min=1.0, L_max=1.2, L_step=0.1); print(len(r['L_arr']), len(r['eigenvalue_sets']))"` → prints `3 3`
  - [x] `python -c "from stab_scan import scan_stabilization, track_levels; r = scan_stabilization(L_min=1.0, L_max=1.5, L_step=0.1); t = track_levels(r); print(t.shape[0], t.shape[1] > 0)"` → `6 True`
  - [x] `find_resonance` on synthetic plateau data returns E_res within 1% of the plateau level (verified in test_stabilization.py)

  **QA Scenarios**:

  ```
  Scenario: scan_stabilization returns correct structure
    Tool: Bash (python -c)
    Preconditions: stab_scan.py exists and is importable
    Steps:
      1. python -c "from stab_scan import scan_stabilization; r = scan_stabilization(L_min=1.0, L_max=1.1, L_step=0.1, N=50); assert 'L_arr' in r and 'eigenvalue_sets' in r and 'mc2' in r; assert len(r['L_arr']) == 2; print('PASS')"
    Expected Result: prints PASS, exit code 0
    Evidence: .sisyphus/evidence/stab-task1-scan-structure.txt

  Scenario: find_resonance returns None gracefully for empty window
    Tool: Bash (python -c)
    Preconditions: stab_scan.py exists
    Steps:
      1. python -c "from stab_scan import scan_stabilization, track_levels, find_resonance; r = scan_stabilization(L_min=1.0, L_max=1.1, L_step=0.1, N=50, E_min_frac=99.0, E_max_frac=100.0); t = track_levels(r); res = find_resonance(r['L_arr'], t, r['mc2']); assert res == (None, None, None), f'Got {res}'; print('PASS')"
    Expected Result: prints PASS, exit code 0 (no crash, graceful None return)
    Evidence: .sisyphus/evidence/stab-task1-scan-none.txt
  ```

  **Evidence to Capture**:
  - [x] `stab-task1-scan-structure.txt`
  - [x] `stab-task1-scan-none.txt`

  **Commit**: YES (groups with Task 2 after both complete)
  - Message: `feat(stab): add stab_scan.py — L-scan, level tracking, resonance detection`
  - Files: `stab_scan.py`

---

- [x] 2. `stab_plot.py` — stabilization graph + resonance wavefunction figure

  **What to do**:

  Implement two plot functions in a new file `stab_plot.py`.

  **Preamble**:
  ```python
  import matplotlib
  matplotlib.use('Agg')  # headless-safe; must be before pyplot import
  import matplotlib.pyplot as plt
  import numpy as np
  from config import M_ELECTRON, C_LIGHT, Z, LAMBDA_SHIELD, KAPPA
  from potential import V
  from mabgps import solve_mabgps
  ```

  **Function 1: `plot_stabilization_graph(L_arr, trajectories, res_idx, mc2, save_path="fig_stabilization.png")`**

  Design specs (from stabalization_plan.md Phase 3 §1):
  - Figure size: `(10, 6)`, dpi=150
  - X-axis: L_scale (L_arr)
  - Y-axis: E/mc² (convert all energies)
  - **Gray thin lines** (`color='lightgray', linewidth=0.8, alpha=0.7, zorder=1`): plot ALL trajectory columns (skip NaN using `np.ma.masked_invalid`)
  - **Thick red line** (`color='red', linewidth=2.5, zorder=3, label=f'Resonance (E={E_res/mc2:.4f} mc²)'`): plot the res_idx column
  - If res_idx is None: plot all gray lines + add text "No resonance found" in center
  - Labels: `xlabel='Scaling parameter $L_{scale}$ (a.u.)'`, `ylabel='Energy $E/mc^2$'`
  - Title: `'Stabilization Graph: Resonance State in Shielded Coulomb Potential (Z=92)'`
  - Annotate plateau region: draw horizontal dashed line at E_res/mc2, annotate with `$E_{res}$`
  - Legend + grid (`alpha=0.3`)
  - `plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close()`

  **Function 2: `plot_resonance_wavefunction(L_opt, E_res, save_path="fig_resonance_wf.png", kappa=KAPPA, Z=Z, lambda_shield=LAMBDA_SHIELD, c=C_LIGHT)`**

  Design specs (from stabalization_plan.md Phase 3 §2):
  - Call `solve_mabgps(L=L_opt, kappa=kappa, Z=Z, lambda_shield=lambda_shield, c=c)` → `(E, vecs, r_interior)`
  - Identify resonance eigenvector: `res_idx_local = np.argmin(np.abs(E - E_res))` (closest eigenvalue)
  - Extract large component: `N2 = len(r_interior); P = vecs[:N2, res_idx_local]` (top half of eigenvector)
  - Normalize: `P = P / np.max(np.abs(P))`
  - V_eff visualization (non-relativistic proxy):
    ```python
    mc2 = M_ELECTRON * c**2
    r_plot = r_interior[r_interior > 0.05]  # skip near-origin singularity (first few points)
    V_pot = V(r_plot, Z=Z, lambda_shield=lambda_shield)
    V_cent = kappa * (kappa + 1) / (2 * r_plot**2)
    V_eff = (V_pot + V_cent) / mc2  # normalized to mc²
    ```
  - **Dual Y-axis figure**: `fig, ax1 = plt.subplots(figsize=(10, 6))`; `ax2 = ax1.twinx()`
  - **Left axis (ax1)**: Plot P(r) in blue — `ax1.plot(r_interior, P, 'b-', linewidth=2, label='$P(r)$ large component')`; restrict x to `r < 20 a.u.`
  - **Right axis (ax2)**: Plot V_eff(r)/mc² in green — `ax2.plot(r_plot, V_eff, 'g--', linewidth=1.5, label='$V_{eff}(r)/mc^2$')`
  - **Horizontal dashed line**: `ax2.axhline(y=E_res/mc2, color='orange', linestyle=':', linewidth=1.5, label=f'$E_{{res}}/mc^2 = {E_res/mc2:.4f}$')`
  - **Shaded pocket**: Find r range where P(r)² > 0.1 * max(P²) as a proxy for the wavefunction peak region; shade with `ax1.axvspan(r_inner, r_outer, alpha=0.1, color='blue', label='Wavefunction pocket')`
  - Labels: `ax1.set_xlabel('r (a.u.)')`, `ax1.set_ylabel('$P(r)$ (normalized)', color='b')`, `ax2.set_ylabel('$V_{eff}(r)/mc^2$', color='g')`
  - Title: `f'Resonance State Wavefunction (E = {E_res/mc2:.4f} mc²,  L_{{opt}} = {L_opt:.3f})'`
  - Combine legends: `lines1, labels1 = ax1.get_legend_handles_labels(); lines2, labels2 = ax2.get_legend_handles_labels(); ax1.legend(lines1+lines2, labels1+labels2, loc='upper right')`
  - `plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close()`

  - If L_opt or E_res is None: save a figure with a centered text message "Resonance not identified — run with broader scan parameters"

  **Must NOT do**:
  - Do NOT use `plt.show()` (headless)
  - Do NOT import from `plot.py` (different concern)
  - Do NOT plot negative-energy eigenvectors (Q component) by accident — large component is top half
  - Do NOT hardcode figure dimensions > `(12, 7)` (paper format)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Primary deliverable is two publication-quality figures requiring careful matplotlib dual-axis layout, color choices, annotation, shading, and legend management
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Tasks 3, 4, F1, F2, F3
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `plot.py:60-147` — Existing `plot_wavefunctions()` pattern: dual subplot, P(r) extraction as `vecs[:N2, idx]`, normalization by `max(abs(P))`, sort by r, mask `r < 20`, `plt.tight_layout(); plt.savefig(); plt.close()`
  - `plot.py:1-57` — `plot_spectrum()` pattern: figure creation, ax styling, tight_layout, savefig pattern
  - `main.py:85-87` — How plot functions are called in this codebase

  **API/Type References**:
  - `potential.V(r, Z, lambda_shield)` — vectorized, returns potential in a.u.
  - `solve_mabgps()` returns `(E_sorted, vecs_sorted, r_interior)`:
    - `r_interior`: shape `(N-2,)`, interior grid points in a.u.
    - `vecs_sorted`: shape `(2*(N-2), 2*(N-2))`, columns are eigenvectors
    - Large component P: `vecs[:N2, idx]` (first N2 rows); small component Q: `vecs[N2:, idx]`
  - `config.KAPPA = 1` (p_{1/2} state with centrifugal term `κ(κ+1)/(2r²) = 1/r²`)

  **Acceptance Criteria**:

  - [x] `python -c "import matplotlib; matplotlib.use('Agg'); from stab_plot import plot_stabilization_graph; import numpy as np; L = np.array([1.0,1.1,1.2]); t = np.column_stack([np.array([1.0,1.01,1.02])*18779, np.array([1.05,1.04,1.03])*18779]); plot_stabilization_graph(L, t, 0, 18779); import os; assert os.path.getsize('fig_stabilization.png') > 20000; print('PASS')"` → prints PASS
  - [x] `fig_stabilization.png` size > 20 KB
  - [x] `fig_resonance_wf.png` size > 20 KB after `run_stab.py` executes

  **QA Scenarios**:

  ```
  Scenario: plot_stabilization_graph runs headless without display error
    Tool: Bash (python -c)
    Preconditions: stab_plot.py exists; matplotlib installed
    Steps:
      1. python -c "
  import matplotlib; matplotlib.use('Agg')
  from stab_plot import plot_stabilization_graph
  import numpy as np
  mc2 = 137.036**2
  L = np.linspace(0.5, 3.0, 10)
  t = np.column_stack([mc2*(1.0 + 0.001*L), mc2*(1.05 - 0.001*L)])
  plot_stabilization_graph(L, t, 1, mc2, 'fig_stabilization.png')
  import os; sz = os.path.getsize('fig_stabilization.png')
  assert sz > 20000, f'File too small: {sz}'
  print('PASS')
  "
    Expected Result: prints PASS, exit code 0, fig_stabilization.png > 20 KB
    Evidence: .sisyphus/evidence/stab-task2-plot1.txt

  Scenario: plot_resonance_wavefunction runs with None inputs (graceful)
    Tool: Bash (python -c)
    Preconditions: stab_plot.py exists
    Steps:
      1. python -c "
  import matplotlib; matplotlib.use('Agg')
  from stab_plot import plot_resonance_wavefunction
  plot_resonance_wavefunction(None, None, save_path='fig_resonance_wf_none.png')
  import os; assert os.path.exists('fig_resonance_wf_none.png'); print('PASS')
  "
    Expected Result: prints PASS, exit code 0, file exists (no crash)
    Evidence: .sisyphus/evidence/stab-task2-plot2-none.txt
  ```

  **Evidence to Capture**:
  - [x] `stab-task2-plot1.txt`
  - [x] `stab-task2-plot2-none.txt`

  **Commit**: YES (commit Tasks 1+2 together after Wave 1 complete)
  - Message: `feat(stab): add stab_plot.py — stabilization graph and resonance wavefunction figures`
  - Files: `stab_plot.py`

---

- [x] 3. `run_stab.py` — entry point

  **What to do**:

  Create `run_stab.py` as the main entry point that orchestrates all 3 phases:

  ```python
  """Entry point for resonance state search via stabilization method."""
  import matplotlib
  matplotlib.use('Agg')

  import numpy as np
  import config as cfg
  from stab_scan import scan_stabilization, track_levels, find_resonance
  from stab_plot import plot_stabilization_graph, plot_resonance_wavefunction


  def main():
      mc2 = cfg.M_ELECTRON * cfg.C_LIGHT ** 2

      print("=" * 60)
      print("Stabilization Method: Resonance State Search")
      print("=" * 60)
      print(f"Parameters: Z={cfg.Z}, kappa={cfg.KAPPA}, lambda={cfg.LAMBDA_SHIELD}, N={cfg.N_POINTS}")
      print(f"L scan: 0.5 to 3.0, step 0.05  ({int((3.0-0.5)/0.05)+1} L values)")
      print(f"Energy window: [0.9, 1.2] mc²")
      print()

      print("Phase 1: Scanning L_scale...")
      scan_result = scan_stabilization()
      total_levels = sum(len(e) for e in scan_result['eigenvalue_sets'])
      print(f"  -> {total_levels} total eigenvalues collected across {len(scan_result['L_arr'])} L values")
      print()

      print("Phase 2: Tracking levels and identifying resonance plateau...")
      trajectories = track_levels(scan_result)
      E_res, L_opt, res_idx = find_resonance(scan_result['L_arr'], trajectories, mc2)

      if E_res is not None:
          print(f"  -> Resonance found: E_res = {E_res/mc2:.6f} mc²  ({E_res:.2f} a.u.)")
          print(f"  -> Optimal scale:   L_opt = {L_opt:.4f}")
      else:
          print("  -> WARNING: No resonance plateau found in the energy window.")
          print("     Figures will be saved with placeholder messages.")
      print()

      print("Phase 3: Generating figures...")
      plot_stabilization_graph(scan_result['L_arr'], trajectories, res_idx, mc2)
      print("  -> Saved: fig_stabilization.png")

      plot_resonance_wavefunction(L_opt, E_res)
      print("  -> Saved: fig_resonance_wf.png")
      print()

      print("=" * 60)
      print("Done.")
      print("=" * 60)


  if __name__ == "__main__":
      main()
  ```

  **Must NOT do**:
  - Do NOT add argparse or CLI flags
  - Do NOT call `bspline.solve_bspline()` (this is MAB-GPS only)
  - Do NOT call `plot.py` functions (separate visualization module)
  - Do NOT change global config state (no `cfg.L_SCALE = ...`)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure boilerplate entry point with no logic; copy-paste from above spec
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (with Task 4)
  - **Blocks**: F1, F2, F3
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `main.py:12-93` — Existing entry point pattern: print header, call solvers, call plot functions, print Done

  **Acceptance Criteria**:
  - [x] `python run_stab.py` exits with code 0 (may take 30-60 seconds for full scan)
  - [x] `fig_stabilization.png` and `fig_resonance_wf.png` exist after running

  **QA Scenarios**:

  ```
  Scenario: run_stab.py runs end-to-end without error
    Tool: Bash
    Preconditions: stab_scan.py, stab_plot.py, run_stab.py all exist
    Steps:
      1. python run_stab.py  (capture stdout)
      2. Check exit code == 0
      3. Check both output files exist and > 20 KB
    Expected Result: exit 0, "Done." in stdout, both PNG files > 20 KB
    Failure Indicators: any Python traceback in stdout/stderr; missing PNG files; file < 20 KB
    Evidence: .sisyphus/evidence/stab-task3-run.txt
  ```

  **Evidence to Capture**:
  - [x] `stab-task3-run.txt` (captured stdout + file size check)

  **Commit**: YES (groups with Task 4)
  - Message: `feat(stab): add run_stab.py — orchestration entry point`
  - Files: `run_stab.py`

---

- [x] 4. `test_stabilization.py` — unit tests + smoke test

  **What to do**:

  Create `test_stabilization.py` with the following test classes. All tests must complete in < 60 seconds total.

  **Class 1: `TestScanStabilization`** — smoke test with real solver (small N)
  ```python
  class TestScanStabilization:
      def test_scan_returns_correct_structure(self):
          """scan_stabilization returns dict with required keys and consistent lengths."""
          result = scan_stabilization(L_min=1.0, L_max=1.2, L_step=0.1, N=50)
          assert 'L_arr' in result and 'eigenvalue_sets' in result and 'mc2' in result
          assert len(result['L_arr']) == 3  # 1.0, 1.1, 1.2
          assert len(result['eigenvalue_sets']) == 3
          assert result['mc2'] > 0

      def test_scan_eigenvalues_finite(self):
          """All returned eigenvalues must be finite (no NaN/inf)."""
          result = scan_stabilization(L_min=1.0, L_max=1.1, L_step=0.1, N=50)
          for eigs in result['eigenvalue_sets']:
              assert np.all(np.isfinite(eigs))

      def test_scan_empty_window(self):
          """Scan with impossibly high energy window returns empty lists."""
          result = scan_stabilization(L_min=1.0, L_max=1.1, L_step=0.1, N=50,
                                       E_min_frac=99.0, E_max_frac=100.0)
          assert all(len(e) == 0 for e in result['eigenvalue_sets'])
  ```

  **Class 2: `TestTrackLevels`** — unit test with synthetic data
  ```python
  class TestTrackLevels:
      def test_perfect_plateau(self):
          """Track 2 levels: one rising, one flat. Trajectories correctly separated."""
          # Synthetic: L=[0.5,1.0,1.5,2.0,2.5], level A=constant 1.05*mc2, level B rises
          mc2 = 137.036**2
          L_arr = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
          eig_sets = [np.sort([1.05*mc2, 1.0*mc2 + i*0.01*mc2]) for i in range(5)]
          result = {'L_arr': L_arr, 'eigenvalue_sets': eig_sets, 'mc2': mc2}
          traj = track_levels(result)
          assert traj.shape[0] == 5
          assert traj.shape[1] >= 2

      def test_handles_empty_window(self):
          """track_levels handles all-empty eigenvalue_sets without crash."""
          mc2 = 137.036**2
          result = {'L_arr': np.array([1.0, 1.1, 1.2]), 'eigenvalue_sets': [[], [], []], 'mc2': mc2}
          traj = track_levels(result)
          assert traj.shape[0] == 3
  ```

  **Class 3: `TestFindResonance`** — unit test with synthetic plateau
  ```python
  class TestFindResonance:
      def test_detects_flat_trajectory(self):
          """find_resonance returns the flat trajectory from synthetic data."""
          mc2 = 137.036**2
          L_arr = np.linspace(0.5, 3.0, 26)
          # Track 0: flat at 1.05*mc2 (resonance)
          # Track 1: rising linearly
          traj = np.column_stack([
              np.full(26, 1.05 * mc2),
              1.0 * mc2 + 0.02 * mc2 * np.arange(26)
          ])
          E_res, L_opt, res_idx = find_resonance(L_arr, traj, mc2)
          assert E_res is not None
          assert res_idx == 0
          assert abs(E_res / mc2 - 1.05) < 0.02  # within 2% of true plateau

      def test_returns_none_for_empty_trajectories(self):
          """find_resonance returns (None, None, None) when no tracks pass coverage filter."""
          mc2 = 137.036**2
          L_arr = np.linspace(0.5, 3.0, 26)
          traj = np.full((26, 3), np.nan)  # all NaN
          result = find_resonance(L_arr, traj, mc2)
          assert result == (None, None, None)
  ```

  **Class 4: `TestPlots`** — non-visual matplotlib test
  ```python
  class TestPlots:
      def test_plot_stabilization_headless(self, tmp_path):
          """plot_stabilization_graph runs under Agg backend without error."""
          import matplotlib; matplotlib.use('Agg')
          from stab_plot import plot_stabilization_graph
          mc2 = 137.036**2
          L = np.linspace(0.5, 3.0, 10)
          traj = np.column_stack([mc2*(1.05 - 0.001*L), mc2*(1.1 + 0.005*L)])
          out = str(tmp_path / "test_stab.png")
          plot_stabilization_graph(L, traj, 0, mc2, save_path=out)
          assert os.path.getsize(out) > 5000

      def test_plot_resonance_wf_none_graceful(self, tmp_path):
          """plot_resonance_wavefunction handles None inputs gracefully."""
          import matplotlib; matplotlib.use('Agg')
          from stab_plot import plot_resonance_wavefunction
          out = str(tmp_path / "test_wf.png")
          plot_resonance_wavefunction(None, None, save_path=out)
          assert os.path.exists(out)
  ```

  **Must NOT do**:
  - Do NOT call `scan_stabilization()` with default N=150 in tests (too slow)
  - Do NOT assert exact numerical resonance energy (depends on physics)
  - Do NOT import from protected files (`bspline`, `main`, `plot`)
  - Tests must NOT require a display (use `matplotlib.use('Agg')`)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires understanding of both the scanning algorithm and synthetic test data design; needs correct NaN handling in assertions
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 3, both in Wave 2)
  - **Parallel Group**: Wave 2 (with Task 3)
  - **Blocks**: F1, F2, F3
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `test_solvers.py:1-65` — Existing test style: class-based, pytest, `import config as cfg`, use `cfg.C_LIGHT` etc.
  - `test_solvers.py:34-43` — Fast test pattern: call `solve_mabgps()` with default params (or override N for speed)

  **Acceptance Criteria**:
  - [x] `pytest test_stabilization.py -q` → all tests PASS, < 60 seconds
  - [x] `pytest test_stabilization.py -v` shows class names `TestScanStabilization`, `TestTrackLevels`, `TestFindResonance`, `TestPlots`
  - [x] No test imports from `bspline`, `main`, `plot` (protected files)

  **QA Scenarios**:

  ```
  Scenario: All stabilization tests pass
    Tool: Bash (pytest)
    Preconditions: stab_scan.py, stab_plot.py, test_stabilization.py all exist
    Steps:
      1. pytest test_stabilization.py -q --tb=short
      2. Check output contains "passed" and no "failed" or "error"
      3. Check total time < 60 seconds
    Expected Result: "X passed in Y.XXs" where Y < 60
    Failure Indicators: any "FAILED" or "ERROR" lines
    Evidence: .sisyphus/evidence/stab-task4-pytest.txt

  Scenario: Protected files untouched (no modification)
    Tool: Bash (git diff or file hash)
    Preconditions: Tasks 1-4 completed
    Steps:
      1. python -c "import hashlib, os; files = ['config.py','mabgps.py','potential.py','bspline.py','main.py','plot.py','test_solvers.py']; [print(f, 'exists:', os.path.exists(f)) for f in files]"
    Expected Result: all 7 files print "exists: True" (not accidentally deleted or renamed)
    Evidence: .sisyphus/evidence/stab-task4-protected.txt
  ```

  **Evidence to Capture**:
  - [x] `stab-task4-pytest.txt`
  - [x] `stab-task4-protected.txt`

  **Commit**: YES (groups with Task 3)
  - Message: `test(stab): add test_stabilization.py — unit + smoke tests for scan/track/detect/plot`
  - Files: `test_stabilization.py`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 3 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Physics Correctness Audit** — `oracle`

  Read `stabalization_plan.md` and `H_issue.md` end-to-end. Check that:
  1. **H_issue fix**: `mabgps.py` does NOT contain `H = 0.5*(H+H.T)`; uses `linalg.eig` + `.real` (not `eigh`)
  2. **Wavefunction smooth**: run oscillation_rate check — must be < 0.5
  3. `stab_scan.py` scans L ∈ [0.5, 3.0] step 0.05 (matches Phase 1 spec)
  4. Energy window `0.9mc² < E < 1.2mc²` implemented as `E_min_frac=0.9, E_max_frac=1.2`
  5. `find_resonance` computes dE/dL derivative and finds the flattest plateau (matches Phase 2 spec)
  6. `fig_stabilization.png`: gray lines for pseudo-continuum, thick red line for resonance
  7. `fig_resonance_wf.png`: dual y-axis with P(r) left + V_eff right + shaded pocket
  8. V_eff formula: `V(r) + kappa*(kappa+1)/(2*r²)` normalized by `mc²`
  9. Run `python run_stab.py` and confirm both PNGs are generated

  Output: `H_issue fix [DONE/MISSING] | Plan compliance [N/N] | Physics checks [N/N] | PNGs [YES/NO] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`

  1. Check `mabgps.py`: confirm `H = 0.5*(H+H.T)` is absent; confirm `linalg.eig` is used
  2. Check all new files (`stab_scan.py`, `stab_plot.py`, `run_stab.py`, `test_stabilization.py`) for:
     - No bare `except:` clauses
     - No unused imports
     - No `print` in library functions (OK in `run_stab.py`)
  3. Run `python -m py_compile mabgps.py stab_scan.py stab_plot.py run_stab.py test_stabilization.py` — all must compile
  4. Run `pytest test_solvers.py -q` — must show **7 passed**
  5. Run `pytest test_stabilization.py -q` — all must pass
  6. Check: `stab_scan.py` imports ONLY from `config`, `mabgps`; `stab_plot.py` imports ONLY from `config`, `potential`, `mabgps`, `matplotlib`, `numpy`

  Output: `Compile [PASS/FAIL] | test_solvers [7/7] | test_stab [N/N] | Import violations [CLEAN/N] | VERDICT`

- [x] F3. **Scope Fidelity Check** — `deep`

  1. **Task 0**: verify `mabgps.py` has EXACTLY 2 changes (remove symmetrization + swap eigh→eig+.real); no other diff
  2. **Task 0**: verify `test_solvers.py` added EXACTLY 1 new test method; no other changes
  3. **Tasks 1-4**: for each, verify implemented code matches "What to do" spec
  4. Check "Must NOT do" compliance for all tasks
  5. Verify absolutely protected files UNCHANGED: `config.py`, `potential.py`, `bspline.py`, `main.py`, `plot.py`
  6. Check no extra files created beyond: `mabgps.py` (mod), `test_solvers.py` (mod), `stab_scan.py`, `stab_plot.py`, `run_stab.py`, `test_stabilization.py`

  Output: `Task 0 surgical [YES/NO] | Tasks 1-4 [N/N compliant] | Protected files [UNCHANGED/N] | Extra files [NONE/N] | VERDICT`

---

## Commit Strategy

- **Wave 0**: `fix(mabgps): remove H symmetrization, restore eig+.real to fix Odd-Even Decoupling` — mabgps.py, test_solvers.py
- **Wave 1**: `feat(stab): add stab_scan.py and stab_plot.py` — stab_scan.py, stab_plot.py
- **Wave 2**: `feat(stab): add run_stab.py and test_stabilization.py` — run_stab.py, test_stabilization.py

---

## Success Criteria

### Verification Commands
```bash
pytest test_solvers.py -q                   # Expected: 7 passed (incl. smoothness test)
python run_stab.py                          # Expected: "Done." in stdout, exit 0
pytest test_stabilization.py -q             # Expected: X passed, 0 failed, < 60s
ls -lh fig_stabilization.png fig_resonance_wf.png  # Expected: both > 20K
python -c "import stab_scan, stab_plot; print('OK')"  # Expected: "OK"
```

### Final Checklist
- [x] `mabgps.py` symmetrization removed; `eig`+`.real` used; 7/7 test_solvers pass
- [x] All "Must Have" present (bug fix, parameterized scan, graceful None returns, headless plots)
- [x] All "Must NOT Have" absent (no argparse, no threshold filtering, no heavy deps, protected files untouched)
- [x] All tests pass (`pytest test_solvers.py` + `pytest test_stabilization.py`)
- [x] Both PNG figures generated by `run_stab.py`
- [x] `stabalization_plan.md` 3-phase spec fully implemented
- [x] `H_issue.md` bug fully resolved
