#!/usr/bin/env python3
"""
Verification script for CCR implementation.
Checks that all components are present and functional.
"""

import sys
import importlib.util

def check_module(name, filepath):
    """Check if a module can be imported."""
    try:
        spec = importlib.util.spec_from_file_location(name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, "✓"
    except Exception as e:
        return False, f"✗ {str(e)[:50]}"

def main():
    print("=" * 70)
    print("CCR Implementation Verification")
    print("=" * 70)
    print()
    
    # Check modules
    modules = [
        ("complex_coordinate_rotation", "complex_coordinate_rotation.py"),
        ("mabgps_ccr", "mabgps_ccr.py"),
        ("test_ccr", "test_ccr.py"),
        ("ccr_demo", "ccr_demo.py"),
    ]
    
    print("Module Imports:")
    print("-" * 70)
    all_ok = True
    for name, filepath in modules:
        ok, status = check_module(name, filepath)
        print(f"  {name:<35} {status}")
        all_ok = all_ok and ok
    
    print()
    
    # Check documentation
    docs = [
        "CCR_IMPLEMENTATION_GUIDE.md",
        "CCR_SUMMARY.md",
    ]
    
    print("Documentation Files:")
    print("-" * 70)
    for doc in docs:
        try:
            with open(doc, 'r') as f:
                lines = len(f.readlines())
            print(f"  {doc:<35} ✓ ({lines} lines)")
        except Exception as e:
            print(f"  {doc:<35} ✗ {str(e)[:30]}")
            all_ok = False
    
    print()
    
    # Check key functions
    print("Key Functions:")
    print("-" * 70)
    
    try:
        from complex_coordinate_rotation import (
            apply_ccr_transformation,
            extract_resonances,
            scan_theta_resonances,
            compute_resonance_trajectory,
            validate_ccr_bound_states,
            V_complex,
        )
        print("  complex_coordinate_rotation:")
        print("    ✓ apply_ccr_transformation")
        print("    ✓ extract_resonances")
        print("    ✓ scan_theta_resonances")
        print("    ✓ compute_resonance_trajectory")
        print("    ✓ validate_ccr_bound_states")
        print("    ✓ V_complex")
    except Exception as e:
        print(f"  complex_coordinate_rotation: ✗ {e}")
        all_ok = False
    
    try:
        from mabgps_ccr import (
            solve_mabgps_ccr,
            solve_mabgps_ccr_with_resonances,
        )
        print("  mabgps_ccr:")
        print("    ✓ solve_mabgps_ccr")
        print("    ✓ solve_mabgps_ccr_with_resonances")
    except Exception as e:
        print(f"  mabgps_ccr: ✗ {e}")
        all_ok = False
    
    print()
    
    # Quick functional test
    print("Functional Test:")
    print("-" * 70)
    
    try:
        from mabgps_ccr import solve_mabgps_ccr_with_resonances
        result = solve_mabgps_ccr_with_resonances(
            N=80, Z=1, lambda_shield=0.1, theta=0.2
        )
        
        print(f"  Solve at θ=0.2: ✓")
        print(f"    - Resonances found: {len(result['energies'])}")
        print(f"    - Bound states: {len(result['bound'])}")
        print(f"    - Grid points: {len(result['r_interior'])}")
        
        if len(result['energies']) > 0:
            print(f"    - First resonance: E={result['energies'][0]:.2f}, Γ={result['widths'][0]:.2e}")
    except Exception as e:
        print(f"  Functional test: ✗ {e}")
        all_ok = False
    
    print()
    print("=" * 70)
    
    if all_ok:
        print("✓ ALL CHECKS PASSED - CCR Implementation Ready")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Please review errors above")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
