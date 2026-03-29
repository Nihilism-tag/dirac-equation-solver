# Decisions (append-only)

## 2026-03-25

- Fixed parameters: Z=92, lambda_shield=0.1, L_SCALE=1.0, ALPHA_MAP=0.1, N_POINTS=100, C_LIGHT=137.036, KAPPA=-1.
- B-spline finite domain: R_MAX=100.0 a.u. with hard-wall boundary (P=Q=0 at r=R_MAX).
- MAB-GPS eigenvalue filtering: keep eigenvalues with |Im(E)| < 1e-8 and sort by real part.
- Validation tolerance: for lambda_shield=0, MAB-GPS ground state (n=1, kappa=-1) relative error < 1e-6 vs analytic.
