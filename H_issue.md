# [Bug] High-frequency oscillatory wavefunction (Odd-Even Decoupling) due to forced Hamiltonian symmetrization

## Description
When running the MAB-GPS solver for the radial Dirac equation ($Z=92, \lambda=0.1$), the ground state energy is computed correctly ($E \approx 0.7416 \, mc^2$). However, the resulting wavefunction plot shows a solid "blue block" instead of a smooth exponential decay. Zooming in reveals that the wavefunction is oscillating wildly between adjacent grid points at the maximum possible frequency (Nyquist mode).

## Root Cause
The issue is caused by the forced symmetrization of the Hamiltonian matrix in `mabgps.py`:
```python
H = 0.5 * (H + H.T)
```
The Chebyshev pseudospectral derivative matrix is intrinsically asymmetric. Forcing it into a symmetric form artificially degrades the global spectral operator into a local central-difference-like operator. 

Because central difference evaluates the derivative of a highly oscillatory Nyquist mode ($+1, -1, +1, -1...$) as exactly zero, it creates a "zero-kinetic-energy trap". The eigensolver greedily superimposes this high-frequency noise onto the physical wavefunction to minimize the total energy, leading to the observed "Odd-Even Decoupling" phenomenon.

## Steps to Reproduce
1. Keep the line `H = 0.5 * (H + H.T)` in `mabgps.py`.
2. Run `main.py` or the plotting script to generate the wavefunction.
3. Observe the extreme sawtooth oscillation in the resulting plot.

## Expected Behavior
The solver should output a smooth, physical $1s_{1/2}$ wavefunction that exponentially decays to zero at the boundary, without high-frequency spatial noise.

## Proposed Fix
1. **Remove** the forced symmetrization: Delete `H = 0.5 * (H + H.T)`.
2. **Revert solver**: Use the standard non-symmetric eigenvalue solver `scipy.linalg.eig(H)` instead of `eigh`.
3. **Filter mathematically**: Extract the real parts of the eigenvalues `eigenvalues = eigenvalues.real` (since spectral truncation may introduce floating-point imaginary noise at the $10^{-14}$ level).