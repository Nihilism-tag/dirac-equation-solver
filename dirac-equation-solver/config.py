"""
Physical constants and configuration parameters for Dirac equation solver.

All quantities in atomic units unless otherwise noted.
Energy convention: TOTAL energy including rest mass (E ~ +c^2 for positive-energy bound states).
"""

# Physical constants (atomic units)
C_LIGHT = 137.036  # Speed of light (a.u.)
M_ELECTRON = 1.0  # Electron mass (a.u.)

# Quantum numbers
KAPPA = 1  # Quantum number for p_{1/2} state (provides centrifugal barrier for resonance search)

# Nuclear and potential parameters
Z = 1  # Nuclear charge (uranium)
LAMBDA_SHIELD = 0.4  # Shielding parameter (NOT fine-structure constant)

# MAB-GPS mapping parameters
ALPHA_MAP = 0.1  # Mapping parameter (controls grid density near origin) - reduced for finer near-origin resolution
L_SCALE = 1.0  # Scaling parameter for radial mapping (optimized for Z=92) - increased for broader domain coverage

# Numerical grid parameters
N_POINTS = 150  # Number of basis functions / grid points (increased for Z=92 accuracy) - reduced for computational efficiency
R_MAX = 100.0  # Maximum radius for B-spline domain (a.u.)
