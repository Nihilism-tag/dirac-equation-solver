# Learnings (append-only)

## 2026-03-25

- Working assumptions locked by plan:
  - Energy convention: **total energy** including rest mass (E ~ +c^2 for positive-energy bound states).
  - Parameter naming: `ALPHA_MAP` (mapping) is NOT fine-structure constant; use `alpha_fs = 1/c` when needed.
  - B-spline baseline must intentionally violate kinetic balance to expose spurious states.

## Task 1 Implementation Notes

### config.py
- Defined all 9 constants with clear comments distinguishing `ALPHA_MAP` (mapping parameter, 0.1) from `alpha_fs = 1/c` (fine-structure constant, ~0.0073).
- Module docstring clarifies atomic units convention and total-energy convention.

### potential.py
- `V(r, Z, lambda_shield)`: Implements V(r) = -Z/r * exp(-lambda*r) with r=0 protection via `np.where(r < 1e-15, -Z*1e15, ...)`.
  - Handles both scalar and array inputs correctly.
  - Returns finite values everywhere (no NaN/inf).
- `analytical_dirac_energy(n, kappa, Z, c)`: Implements hydrogen-like Dirac formula with **normalized output** (units of mc²).
  - Key insight: Formula naturally gives E in atomic units (mc² = c² ≈ 18778), so we divide by c² to normalize.
  - For Z=1, n=1, kappa=-1: E ≈ 0.99997 (matches expected ~0.99997).

### Verification Results
- V(r) monotonicity: ✓ (three negative values, strictly decreasing)
- V(r=0) protection: ✓ (finite value, no crash)
- Analytical energy (hydrogen): ✓ (E ≈ 0.99997, within 0.999-1.0 range)

### Gotchas
- RuntimeWarning about divide-by-zero in V() is expected (numpy evaluates both branches before np.where selection). No functional impact.
- Energy normalization was critical: plan expects E in units of mc²=1, not atomic units.

## Task 1 Completion Verification (2026-03-25)

### Files Created/Verified
- ✓ `config.py`: All 9 constants defined with exact values
- ✓ `potential.py`: Both `V()` and `analytical_dirac_energy()` exported

### Verification Results
- ✓ V(r) monotonicity test: [-83.245, -37.662, -11.160] (strictly decreasing)
- ✓ V(r=0) singularity protection: Returns finite value (-9.2e+16), no crash
- ✓ Analytical energy (Z=1, n=1, κ=-1): E ≈ 0.99997 (within expected range)
- ✓ No TODO/FIXME comments in source files
- ✓ Python syntax valid (py_compile passed)
- ✓ All functions have proper docstrings describing atomic units and total-energy convention

### Key Implementation Details
- `V()` uses `np.where(r < 1e-15, -Z*1e15, ...)` for r=0 protection
- `analytical_dirac_energy()` returns **normalized energy** (units of mc²=1)
- Parameter naming clearly separates `ALPHA_MAP` (0.1, mapping) from `alpha_fs = 1/c` (fine-structure constant)
- RuntimeWarning about divide-by-zero is expected (numpy evaluates both branches before selection)

### Status
**COMPLETE** — Foundation module ready for Task 2/3 (B-spline and MAB-GPS solvers)

## Task 1 Final Verification (2026-03-25 — Comprehensive)

### All Acceptance Criteria Met

**Scenario 1: V(r) Monotonicity**
- ✓ V([1, 2, 5]) = [-83.245, -37.662, -11.160]
- ✓ Strictly decreasing, all negative
- ✓ No NaN/inf

**Scenario 2: V(r=0) Singularity Protection**
- ✓ V(0) = -9.2e+16 (finite)
- ✓ Program does not crash
- ✓ Exit code 0

**Scenario 3: Analytical Energy (Z=1, n=1, κ=-1)**
- ✓ E = 0.9999733740
- ✓ Within expected range 0.999 < E < 1.0
- ✓ Matches hydrogen-like Dirac formula

### Implementation Quality

- ✓ All 9 constants defined with exact values
- ✓ Parameter naming unambiguous: ALPHA_MAP (0.1) ≠ alpha_fs (1/c ≈ 0.0073)
- ✓ Both functions have comprehensive docstrings
- ✓ Docstrings describe atomic units and total-energy convention
- ✓ No TODO/FIXME comments
- ✓ Python syntax valid (py_compile passed)
- ✓ Functions handle both scalar and array inputs
- ✓ All outputs are finite (no NaN/inf)

### Key Design Decisions

1. **Energy Normalization**: `analytical_dirac_energy()` returns E in units of mc² (normalized), not raw atomic units. This matches the plan's total-energy convention.

2. **Singularity Protection**: `V()` uses `np.where(r < 1e-15, -Z*1e15, ...)` to handle r=0. The RuntimeWarning about divide-by-zero is expected (numpy evaluates both branches before selection) and has no functional impact.

3. **Parameter Separation**: Explicitly documented that ALPHA_MAP (mapping parameter, 0.1) is NOT the fine-structure constant (1/c ≈ 0.0073). This prevents confusion in downstream solvers.

### Foundation Ready for Wave 2

Task 1 is **COMPLETE** and provides a stable API for:
- Task 2 (B-spline solver): Uses `V()` and constants
- Task 3 (MAB-GPS solver): Uses `V()`, `analytical_dirac_energy()`, and constants
- Task 4 (Integration): Uses all exports for validation and plotting

## Task 2: Fix V() Divide-by-Zero Warning (2026-03-25)

### Problem
`V(r, Z, lambda_shield)` emitted `RuntimeWarning: divide by zero encountered in divide` when called with arrays containing 0.0, even though the result was correct. Root cause: `np.where()` evaluates both branches before selecting, triggering the warning on `-Z / r[~mask]`.

### Solution
Replaced `np.where()` with explicit masking: allocate result array, fill protected region (r < 1e-15) with -Z*1e15, then compute division only on nonzero entries. Returns scalar for scalar input, array for array input.

### Verification
- ✅ `python -W error -c "from potential import V; import numpy as np; print(V(np.array([0.0,1.0]),92,0.1))"` exits 0 with no warning
- ✅ V(0) = -9.2e+16 (unchanged)
- ✅ V(1) ≈ -83.245 (unchanged)
- ✅ Scalar and array inputs both work
- ✅ Removed unused import C_LIGHT
