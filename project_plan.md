# System Prompt / Project Context for AI Coding Agent
**Project Title**: Numerical Solution of Dirac Equation: MAB-GPS vs. Standard B-spline
**Objective**: Implement and compare the MAB-GPS (Mapping with Algebraic Basis - Generalized Pseudospectral) method against the Standard B-spline Galerkin method for solving the single-electron radial Dirac equation with a shielded Coulomb potential. The goal is to demonstrate that MAB-GPS successfully avoids "spurious states" (variational collapse), whereas the standard B-spline method without kinetic balance fails.

## 1. Environment & Dependencies
* **Language**: Python 3.10+
* **Libraries**: `numpy`, `scipy` (for `linalg.eig`, `linalg.eigh`, and orthogonal polynomials), `matplotlib` (for visualization).

## 2. Mathematical & Physical Formulation
The radial Dirac equation is given by:
$$H \psi = E \psi$$
Where $\psi(r) = (P(r), Q(r))^T$ represents the large and small components. The Hamiltonian is:
$$H = \begin{pmatrix} V(r) + mc^2 & c(-\frac{d}{dr} + \frac{\kappa}{r}) \\ c(\frac{d}{dr} + \frac{\kappa}{r}) & V(r) - mc^2 \end{pmatrix}$$

* **Constants (Atomic Units)**: $c \approx 137.036$, $m = 1$.
* **Quantum Number**: $\kappa = -1$ (for $s_{1/2}$ state).
* **Potential (Shielded Coulomb)**: $V(r) = -\frac{Z}{r} e^{-\lambda r}$

---

## 3. Agent Execution Tasks

### Task 1: Foundation & Potential Module
* **Action**: Create a Python module to define the physical constants and the shielded Coulomb potential function `V(r, Z, lambda_param)`.
* **Note**: Handle the Coulomb singularity at $r \rightarrow 0$ carefully (e.g., add a tiny epsilon $\epsilon = 10^{-15}$ if dividing by zero, though MAB-GPS mapping should naturally avoid exact zero if designed correctly).

### Task 2: Standard B-spline Implementation (Baseline)
* **Action**: Implement the standard B-spline Galerkin method to solve the Dirac equation.
* **Details**:
  1. Generate knot sequences and B-spline basis functions $B_i(r)$.
  2. Expand $P(r)$ and $Q(r)$ using the *same* basis set $B_i(r)$ (intentionally violating kinetic balance).
  3. Construct the overlap matrix $\mathbf{S}$ and Hamiltonian matrix $\mathbf{H}$.
  4. Solve the generalized eigenvalue problem: $\mathbf{H c} = E \mathbf{S c}$ using `scipy.linalg.eigh`.
* **Expected Output**: A function returning the full energy spectrum. It must include non-physical spurious states falling inside the energy gap $[-mc^2, mc^2]$.

### Task 3: MAB-GPS Implementation (Proposed Solution)
* **Action**: Implement the equilibrium MAB-GPS method.
* **Details**:
  1. Compute $N$ roots of the Legendre polynomial $x_i \in [-1, 1]$.
  2. Apply the nonlinear algebraic mapping to physical space $r \in [0, \infty)$:
     $$r(x) = L \frac{1+x}{1-x+\alpha}$$
     *(Define $L$ as a scaling parameter and $\alpha$ to control grid density near the origin).*
  3. Construct the pseudospectral first-derivative matrix $\mathbf{D}$ using the analytic derivative of Lagrange interpolating polynomials and the chain rule $\frac{d}{dr} = \frac{dx}{dr} \frac{d}{dx}$.
  4. Assemble the $2N \times 2N$ asymmetric Hamiltonian matrix $\mathbf{H}$.
  5. Solve the standard eigenvalue problem: $\mathbf{H c} = E \mathbf{c}$ using `scipy.linalg.eig`.
* **Expected Output**: A function returning a clean physical energy spectrum without any spurious states.

### Task 4: Visualization & Analysis
* **Action**: Create a plotting script using `matplotlib` to compare the two methods.
* **Details**:
  1. **Spectrum Scatter Plot**: Plot the eigenvalue indices (x-axis) vs. Energy $E$ (y-axis) in the range $[-2mc^2, 2mc^2]$. Overlay the B-spline results (showing spurious states) and MAB-GPS results (clean spectrum).
  2. **Wavefunction Plot**: Extract the eigenvector of a spurious state from the B-spline method and plot its highly oscillatory behavior near the origin. Compare it with the smooth, physically correct ground state wavefunction from MAB-GPS.