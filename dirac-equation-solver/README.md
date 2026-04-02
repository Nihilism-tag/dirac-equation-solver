# Dirac Equation Solver

A comprehensive numerical framework for solving the single-electron radial Dirac equation with screened Coulomb potential, designed for studying resonance states in relativistic quantum systems.

## Features

- **Three numerical methods**: B-spline finite element, MAB-GPS pseudospectral, and stabilization methods
- **Complex Coordinate Rotation (CCR)**: Resonance state identification in the positive energy continuum
- **Interactive visualization**: Real-time exploration of complex energy spectra
- **Comprehensive testing**: 39+ tests covering numerical stability and boundary conditions
- **Detailed documentation**: Algorithm explanations, implementation guides, and validation results

## Quick Start

### Installation

```bash
cd dirac-equation-solver
pip install numpy scipy matplotlib pytest
```

### Basic Usage

**Run stabilization analysis**:
```bash
python run_stab.py
```
Outputs: `fig_stabilization.png`, `fig_resonance_wf.png`

**Compare MAB-GPS vs B-spline methods**:
```bash
python main.py
```
Outputs: `spectrum.png`, `wavefunction.png`

### CCR Resonance Search Workflow

**Step 1: Perform theta scan to collect complex energy data**
```bash
python ccr_scan.py --theta-start 0.05 --theta-stop 0.50 --theta-step 0.02 --out ccr_data.npz
```

**Step 2: Interactive visualization of complex energy spectrum**
```bash
python ccr_interactive_plot.py --in ccr_data.npz
```
Interactive controls: zoom (z key), reset (r key), save (s key)

**Step 3: Headless plotting (for CI/server environments)**
```bash
MPLBACKEND=Agg python ccr_interactive_plot.py --in ccr_data.npz --no-show --out ccr_plot.png
```

### Run Demos
```bash
python ccr_demo.py
```
Includes 4 comprehensive demonstrations:
1. Fixed-theta resonance finding
2. Theta-scan observing resonance emergence
3. Resonance trajectory tracking
4. Complex-plane visualization

### Run Tests
```bash
pytest test_solvers.py test_stabilization.py test_ccr_scan.py -q
pytest test_ccr.py -v
```

## Project Structure

```
dirac-equation-solver/
├── config.py              # Physical constants and numerical parameters (atomic units)
├── potential.py           # Potential functions and analytical energy formulas
├── bspline.py            # B-spline finite element solver (benchmark)
├── mabgps.py             # MAB-GPS pseudospectral solver (core algorithm with CGL nodes)
├── complex_coordinate_rotation.py  # CCR transformation and resonance extraction
├── mabgps_ccr.py         # CCR-enabled MAB-GPS solver
├── stab_scan.py          # Stabilization scan and level tracking
├── stab_plot.py          # Stabilization visualization (stabilization plot + resonance wavefunction)
├── run_stab.py           # Stabilization method entry point
├── ccr_scan.py           # CCR theta scan and complex energy data collection
├── ccr_interactive_plot.py  # Interactive complex energy scatter plot
├── ccr_demo.py           # CCR demonstration script (4 complete examples)
├── test_solvers.py       # Core solver test suite (7 tests)
├── test_stabilization.py # Stabilization method test suite (9 tests)
├── test_ccr.py           # Comprehensive CCR test suite (13 tests)
├── test_ccr_scan.py      # CCR scan test
├── verify_ccr.py         # CCR verification script
├── main.py               # MAB-GPS vs B-spline comparison
├── plot.py               # Basic plotting functions
└── pic/                  # Generated images directory
```

## Documentation

- **[README_zh.md](README_zh.md)**: Chinese version of this document
- **[工程说明.md](工程说明.md)**: Complete engineering documentation in Chinese (algorithm principles, strategy choices, verification results, defect fixes)
- **[CCR_SUMMARY.md](CCR_SUMMARY.md)**: CCR implementation summary in Chinese
- **[CCR_IMPLEMENTATION_GUIDE.md](CCR_IMPLEMENTATION_GUIDE.md)**: CCR implementation guide in Chinese
- **[FILES_MANIFEST.md](FILES_MANIFEST.md)**: Detailed file manifest in Chinese

## Technical Highlights

1. **CGL nodes with boundary truncation**: Strict enforcement of Dirichlet boundary conditions
2. **Asymmetric solving**: Using `eig+.real` to avoid even-odd decoupling (Nyquist oscillations)
3. **Three-stage stabilization**: L-scale scan → level tracking → resonance identification
4. **Dual-method comparison**: MAB-GPS (global spectral) vs B-spline (local finite element)
5. **Complex coordinate rotation**: Transforms resonances in continuum into discrete complex eigenvalues

## Physical System

Current working parameters (from `config.py`):
- **Nuclear charge**: Z=1
- **Screening parameter**: λ=0.1
- **Quantum number**: κ=1 (p₁/₂ state, provides centrifugal barrier)
- **Energy range**: Resonance search in continuum

These parameters can be modified in `config.py` or overridden at runtime via `ccr_scan.py` options (`--N`, `--L`, `--alpha-map`).

## Dependencies

- **Required**: numpy, scipy, matplotlib, pytest
- **Standard library**: argparse, pathlib, datetime, tempfile, importlib, typing

## License

This project is open source and available for academic and research use.

## Citation

If you use this code in your research, please cite:

```
Dirac Equation Solver: A numerical framework for relativistic quantum resonance studies.
GitHub: https://github.com/Nihilism-tag/dirac-equation-solver
```

## Contact

For questions or contributions, please open an issue on the [GitHub repository](https://github.com/Nihilism-tag/dirac-equation-solver).

---

**Documentation Version**: v3.0 (complete stabilization method version)  
**Generated Date**: March 26, 2026  
**Project Repository**: https://github.com/Nihilism-tag/dirac-equation-solver