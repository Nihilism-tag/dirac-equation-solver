
## Task 1: Config Parameter Updates
Updated three MAB-GPS mapping parameters in config.py:
- ALPHA_MAP: 0.2 → 0.1 (finer near-origin grid resolution)
- L_SCALE: 0.1 → 1.0 (broader radial domain coverage)
- N_POINTS: 200 → 150 (computational efficiency trade-off)
All other constants (Z, LAMBDA_SHIELD, KAPPA, C_LIGHT, M_ELECTRON, R_MAX) preserved unchanged.
## Execution Summary (2026-03-26)

### CGL Implementation Success
- CGL nodes: analytic formula `-cos(kπ/(N-1))` works perfectly, includes endpoints
- Chebyshev derivative matrix (Trefethen p.53): diagonal sum rule critical for stability
- Boundary truncation: interior_idx = 1..N-2 (N-2 = 148 points for N=150)

### Physics Fixes Verified
1. **Defect 1 (r_max too small)**: Fixed ✓
   - New r_max = 2L/alpha = 2*1.0/0.1 = 20 a.u. (vs 1.0 previously)
   - P(r_max) = 6.40e-06 << 0.01 (proper decay)

2. **Defect 2 (non-Hermitian H)**: Fixed ✓
   - Switched from `linalg.eig` → `linalg.eigh` (real symmetric)
   - Symmetrize after truncation: H = 0.5*(H+H.T)
   - Result: 296 eigenvalues, all real, no filtering needed
   - len(E) = 2*(N-2) = 2*148 = 296 ✓

3. **Defect 3 (no BC at r=0)**: Fixed ✓
   - Interior nodes exclude r_all[0]=0 and r_all[N-1]=r_max
   - r_min = 1.06e-04 > 0 (regularity enforced)

### Numerical Accuracy
- Ground state energy error: 3.29e-08 << 1e-6 ✓
- Better than defective GL implementation (fake pass at 4.61e-7)

### Test Suite
- All 6 pytest tests pass (100%)
- test_mabgps_no_spurious updated: expects 2*(N-2) eigenvalues, no imaginary filter
- Bound states: ~28 (physical), clean spectrum

### Files Modified
- config.py: L=1.0, alpha=0.1, N=150 ✓
- mabgps.py: CGL + truncation + symmetrize + eigh ✓
- test_solvers.py: updated test assertions ✓
- plot.py: N2=len(r_mab) for interior grid ✓
- No scope creep (bspline, potential, main unchanged) ✓

### Critical Insight
The "fake pass" in original GL implementation was due to numerical cancellation—
energy error happened to be small because r_max=1.0 was too restrictive, masking the 
wave function decay issue. CGL + proper domain (r_max=20) fixes physics while maintaining accuracy.
