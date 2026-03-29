# Resonance State Search and Visualization Plan (Stabilization Method)

## Phase 1: Data Acquisition (Automated Stabilization Scanning)
**Objective**: Calculate eigenvalues at different spatial scales to find "resonance plateaus" that are insensitive to boundaries.
1. **Build Parameter Grid**: Set an $L_{scale}$ scanning interval in `config.py` (e.g., from $L=0.5$ to $L=3.0$ with a step of $0.05$).
2. **Batch Solving**: Write an automated script to loop through $L_{scale}$ and call `solve_mabgps()` from `mabgps.py`.
3. **Data Storage**: Save only the real eigenvalue sequences located in the energy gap or low-energy positive continuum (e.g., $0.9 \, mc^2 < E < 1.2 \, mc^2$).

## Phase 2: Automated Identification (Capturing the Resonance State)
**Objective**: Use algorithms instead of the naked eye to accurately lock onto the resonance energy.
1. **Calculate Energy Gradients**: Compute the derivative $dE/dL_{scale}$ for each energy level sequence with respect to $L_{scale}$.
2. **Lock the Stationary Point**: Find the energy interval where the absolute value of the derivative is minimized (i.e., the flattest part of the curve). The energy corresponding to this plateau is the **resonance energy $E_{res}$**.
3. **Extract Optimal Scale**: Record the optimal mapping parameter $L_{opt}$ corresponding to the center of this plateau for subsequent wavefunction extraction.

## Phase 3: Core Visualization Design
Once the resonance state is found, we need to output two highly academic figures to demonstrate it.

### 1. Stabilization Graph
**Physical Meaning**: Visually demonstrate the descent of continuum states and the stability of the resonance state. 
- **X-axis**: Scaling parameter $L_{scale}$ (representing the size of the computational "box").
- **Y-axis**: Eigenvalue energy $E/mc^2$.
- **Visual Presentation**:
  - Use thin gray lines to draw all the "pseudo-continuum states" that bend sharply downwards as $L_{scale}$ increases.
  - Use a **striking thick red line** to highlight the "resonance state plateau" running through them as an almost horizontal straight line.

### 2. Resonance State Wavefunction and Effective Barrier Graph
**Physical Meaning**: Show the quasi-bound characteristics of the electron "trapped" by the local barrier and the quantum tunneling effect.
- **Environment Setup**: Fix the parameter to the newly found $L_{opt}$ and solve once more to extract the eigenvectors.
- **Dual Y-axis Plotting**:
  - **Left Y-axis (Wavefunction)**: Plot the large component wavefunction $P(r)$ of the resonance state. It should have a tall bound-state-like peak near the origin; after penetrating the barrier, the tail will show tiny continuous oscillations.
  - **Right Y-axis (Potential Energy)**: Overlay the **effective potential energy curve $V_{eff}(r)$** of the Dirac equation.
- **Visual Presentation**: Use a shaded area to mark the inner "pocket" of the effective barrier, aligning the peak of the wavefunction perfectly inside the pocket to clearly reveal the physical origin of the resonance state!