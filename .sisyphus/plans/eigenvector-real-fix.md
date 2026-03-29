# Eigenvector Real-Cast Fix: `eigenvectors = eigenvectors.real`

## TL;DR

> **Quick Summary**: Add one line — `eigenvectors = eigenvectors.real` — to `solve_mabgps()` in `dirac-equation-solver/mabgps.py`. Currently eigenvalues are cast to real but eigenvectors remain complex dtype (~1e-14 imaginary noise). This makes all downstream wavefunction arrays consistently real-valued without relying on explicit `.real` calls in calling code.
>
> **Deliverables**:
> - `dirac-equation-solver/mabgps.py` *(modified)* — add `eigenvectors = eigenvectors.real` after eigenvalue real-cast
>
> **Estimated Effort**: Quick (1-line surgical change)
> **Parallel Execution**: NO — single sequential task
> **Critical Path**: Task 1 → F1

---

## Context

### Original Request

`new_fix.md` in the project root describes the fix for Odd-Even Decoupling (Nyquist sawtooth oscillation in wavefunctions). The eigenvalue portion of that fix (`eigenvalues = eigenvalues_complex.real`) was already applied in `stabilization.md` Task 0. However, one part was not yet implemented: `eigenvectors = eigenvectors.real`.

### Current State of `dirac-equation-solver/mabgps.py` (lines 149–154)

```python
eigenvalues_complex, eigenvectors = linalg.eig(H)
eigenvalues = eigenvalues_complex.real
# eigenvectors still complex dtype — imaginary parts ~1e-14 numerical noise

sort_idx = np.argsort(eigenvalues)
E_sorted = eigenvalues[sort_idx]
vecs_sorted = eigenvectors[:, sort_idx]   # ← complex128, not float64
```

### Target State (per `new_fix.md`)

```python
eigenvalues_complex, eigenvectors = linalg.eig(H)
eigenvalues = eigenvalues_complex.real
eigenvectors = eigenvectors.real          # ← NEW: cast to float64

sort_idx = np.argsort(eigenvalues)
E_sorted = eigenvalues[sort_idx]
vecs_sorted = eigenvectors[:, sort_idx]   # ← now float64
```

### Why This Matters

- **Consistency**: `E_sorted` is float64 but `vecs_sorted` is complex128 — asymmetric return types are confusing.
- **Downstream correctness**: `stab_plot.py` accesses `vecs[:N2, res_idx_local]` without `.real` — gets complex array silently. Plotting complex arrays may cause matplotlib warnings or unexpected behavior.
- **Physical correctness**: With correct boundary conditions and a real Hamiltonian, eigenvectors must be real. The ~1e-14 imaginary parts are pure floating-point noise.

### Metis Review (implicit — trivial task)

No gaps identified. `new_fix.md` fully specifies the change. All downstream callers either:
- Already call `.real` explicitly (`test_solvers.py`, `plot.py`) — unaffected
- Do NOT call `.real` (`stab_plot.py:vecs[:N2, ...]`) — now safe

---

## Work Objectives

### Core Objective

Make `solve_mabgps()` return real-dtype eigenvectors by adding the single missing line `eigenvectors = eigenvectors.real`.

### Concrete Deliverables

- `dirac-equation-solver/mabgps.py`: one new line between the eigenvalue cast and the sort step

### Definition of Done

- [ ] `vecs_sorted` dtype is `float64` (not `complex128`)
- [ ] All 16 existing tests still pass (`pytest` in `dirac-equation-solver/`)

### Must Have

- The single line `eigenvectors = eigenvectors.real` inserted at the correct location
- No other changes to `mabgps.py`
- All existing tests remain PASSING

### Must NOT Have (Guardrails)

- **禁止**修改任何其他文件 — `config.py`, `potential.py`, `bspline.py`, `main.py`, `plot.py`, `stab_scan.py`, `stab_plot.py`, `run_stab.py`, `test_solvers.py`, `test_stabilization.py` must all remain UNCHANGED
- **禁止**修改 `mabgps.py` 的任何其他行 — only the one insertion
- **禁止**重新引入 `H = 0.5*(H+H.T)` 对称化或 `eigh` 求解器
- **禁止**添加虚部阈值过滤逻辑 (`|Im| < 1e-8`) — 仅使用 `.real`

---

## Verification Strategy

### Test Decision

- **Infrastructure exists**: YES (`pytest`, `test_solvers.py`, `test_stabilization.py`)
- **Automated tests**: Tests-after (verify existing 16 tests still pass)
- **Framework**: pytest

### QA Policy

- Verify `vecs_sorted` dtype via python one-liner
- Run full pytest suite to confirm no regressions

---

## Execution Strategy

```
Task 1: Add `eigenvectors = eigenvectors.real` to mabgps.py  [quick]
    ↓
F1: Verify dtype + run pytest (16 tests)
```

---

## TODOs

- [ ] 1. Add `eigenvectors = eigenvectors.real` to `dirac-equation-solver/mabgps.py`

  **What to do**:

  In `dirac-equation-solver/mabgps.py`, find the block starting at line 149:
  ```python
  eigenvalues_complex, eigenvectors = linalg.eig(H)
  eigenvalues = eigenvalues_complex.real
  ```

  Insert one line immediately after `eigenvalues = eigenvalues_complex.real`:
  ```python
  eigenvalues_complex, eigenvectors = linalg.eig(H)
  eigenvalues = eigenvalues_complex.real
  eigenvectors = eigenvectors.real          # ← INSERT THIS LINE
  ```

  That is the **entire change**. Nothing else in the file should be touched.

  **Must NOT do**:
  - Do NOT modify any other line in `mabgps.py`
  - Do NOT modify any other file
  - Do NOT re-introduce symmetrization or `eigh`
  - Do NOT add imaginary threshold filtering

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single-line insertion, fully specified, no logic changes
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (only task)
  - **Blocks**: F1
  - **Blocked By**: None (start immediately)

  **References**:
  - `dirac-equation-solver/mabgps.py:149-154` — exact target block
  - `new_fix.md:37-49` — authoritative specification of the complete fix block

  **Acceptance Criteria**:

  **QA Scenarios**:

  ```
  Scenario: eigenvectors dtype is float64 after fix
    Tool: Bash (python -c), run from dirac-equation-solver/
    Steps:
      1. python -c "
  import sys; sys.path.insert(0, '.')
  from mabgps import solve_mabgps
  E, vecs, r = solve_mabgps()
  print('vecs dtype:', vecs.dtype)
  assert vecs.dtype == float, f'Expected float64, got {vecs.dtype}'
  print('PASS')
  "
    Expected Result: "vecs dtype: float64", "PASS"
    Failure Indicators: "complex128" in output; AssertionError
    Evidence: .sisyphus/evidence/eigvec-fix-dtype.txt

  Scenario: All 16 existing tests still pass
    Tool: Bash (pytest), run from dirac-equation-solver/
    Steps:
      1. pytest test_solvers.py test_stabilization.py -q --tb=short
    Expected Result: "16 passed" (or more), 0 failed
    Failure Indicators: any "FAILED" or "ERROR"
    Evidence: .sisyphus/evidence/eigvec-fix-pytest.txt
  ```

  **Evidence to Capture**:
  - [ ] `.sisyphus/evidence/eigvec-fix-dtype.txt`
  - [ ] `.sisyphus/evidence/eigvec-fix-pytest.txt`

  **Commit**: YES
  - Message: `fix(mabgps): cast eigenvectors to real dtype to match eigenvalues`
  - Files: `dirac-equation-solver/mabgps.py`

---

## Final Verification Wave

- [ ] F1. **Regression Check** — `quick`

  Run from `dirac-equation-solver/`:
  1. Verify dtype: `python -c "from mabgps import solve_mabgps; _,v,_=solve_mabgps(); print(v.dtype); assert v.dtype==float"`
  2. Run `pytest test_solvers.py test_stabilization.py -q`
  3. Confirm: 16 passed, 0 failed, vecs dtype = float64

  Output: `dtype [float64/complex128] | Tests [16/16] | VERDICT: APPROVE/REJECT`

---

## Commit Strategy

- **Commit 1**: `fix(mabgps): cast eigenvectors to real dtype to match eigenvalues` — `dirac-equation-solver/mabgps.py`

---

## Success Criteria

```bash
# Run from dirac-equation-solver/
python -c "from mabgps import solve_mabgps; _,v,_=solve_mabgps(); assert v.dtype==float; print('dtype OK:', v.dtype)"
pytest test_solvers.py test_stabilization.py -q  # Expected: 16 passed
```

### Final Checklist

- [ ] `eigenvectors = eigenvectors.real` present in `mabgps.py` between lines 150-151
- [ ] `vecs_sorted` dtype = float64
- [ ] All 16 tests pass
- [ ] No other files modified
