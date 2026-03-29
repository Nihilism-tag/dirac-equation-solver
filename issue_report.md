# Dirac Equation Solver (MAB-GPS) Code Defects and Repair Suggestions

> **⚠️ Core Warning**: Although the current MAB-GPS solver passes the energy eigenvalue accuracy test, its underlying grid mapping and boundary condition handling have serious flaws. This results in completely unphysical wavefunctions exhibiting severe numerical truncation and abrupt jumps.

---

## I. Core Defect Analysis

### 1. Grid Generation Missing Physical Boundaries (Boundary Condition Failure)
The current code uses **Legendre-Gauss nodes**:

```python
x_nodes, _ = np.polynomial.legendre.leggauss(N)
r_nodes = L * (1 + x_nodes) / (1 - x_nodes + alpha_map)
```

- **Physical Conflict**: `leggauss` nodes lie strictly in the open interval `(-1, 1)`. After mapping to physical space, the radial grid `r_nodes` can never reach the true origin `r = 0`.
- **Fatal Consequence**: Without the origin in the grid, the solver cannot impose **Dirichlet Boundary Conditions** (i.e., the wavefunction must be exactly 0 at the origin). The solver operates "freely" near the origin, leading to an unphysical, vertical cliff-like drop in the wavefunction.

### 2. Non-Hermitian Pseudospectral Derivative Matrix (Extreme Numerical Instability)
The code constructs the derivative matrix directly using the barycentric Lagrange interpolation formula:

```python
D[i, j] = (w[j] / w[i]) / (x_nodes[i] - x_nodes[j])
```

- **Physical Conflict**: This directly constructed derivative matrix is asymmetric. When substituted into the Dirac Hamiltonian $H$, the entire matrix becomes **Non-Hermitian**.
- **Fatal Consequence**: Quantum mechanics requires the Hamiltonian to be Hermitian to guarantee real eigenvalues and orthogonal completeness. Forcing `scipy.linalg.eig` to solve a non-Hermitian matrix easily triggers severe numerical degeneration. The code even uses `np.abs(eigenvalues.imag) < 1e-8` to violently discard imaginary parts, masking the underlying ill-conditioned nature of the matrix.

### 3. "Fake Pass" in Test Cases
- **Phenomenon**: In `main.py`, the ground state energy test for $\lambda=0$ passes perfectly (error $< 10^{-6}$).
- **Cause**: With a sufficient number of nodes ($N=200$), the asymmetric collocation method can indeed converge its **eigenvalues** to the true physical energy. However, due to the lack of boundary constraints and Hermitian guarantees, the corresponding **eigenvectors (wavefunctions)** completely collapse. This creates a bizarre scenario: "correct energy, completely wrong wavefunction."

---

## II. Repair Suggestions

To thoroughly resolve these issues, the following refactoring of `mabgps.py` is highly recommended:

### Plan A: Change Collocation Points and Force Boundary Conditions (Recommended, Moderate Effort)

1. **Change Node Type**: 
   Use **Legendre-Gauss-Lobatto (LGL) nodes** instead of `leggauss`. LGL nodes include the endpoints of the closed interval `[-1, 1]`, which perfectly cover `r=0` to the truncation radius after mapping.
2. **Matrix Truncation (Forced Boundary)**: 
   After assembling the full $2N \times 2N$ Dirac Hamiltonian, **manually delete** the rows and columns corresponding to the first and last nodes (i.e., at `r=0` and $r \to \infty$). This mathematically forces the wavefunction values at the boundaries to be exactly 0.

### Plan B: Galerkin Method Symmetrization

- Introduce integration weights (integration measure) to construct a symmetric Hamiltonian matrix $H$ and overlap matrix $S$.
- Transform the standard eigenvalue problem into a **Generalized Eigenvalue Problem**: $Hc=ESc$.
- This plan fundamentally guarantees the Hermiticity of the matrix and completely eliminates the imaginary eigenvalue issue.

---

## III. Summary

The current MAB-GPS implementation is a **"half-finished product"**. It successfully leverages the exponential convergence of pseudospectral methods to calculate energies, but critically misses the two foundational pillars of quantum mechanical computations: **boundary conditions** and **Hamiltonian Hermiticity**. It is advised to immediately pause subsequent physical calculations and prioritize refactoring the underlying grid mapping and matrix assembly logic.