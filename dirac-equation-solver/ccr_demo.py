"""
Complex Coordinate Rotation (CCR) Demonstration

Shows how to use the CCR module to find resonance states in the Dirac equation.
Includes:
1. Basic resonance finding at fixed theta
2. Theta scanning to track resonance emergence
3. Visualization of resonance properties
"""

import numpy as np
import matplotlib.pyplot as plt
from mabgps_ccr import solve_mabgps_ccr, solve_mabgps_ccr_with_resonances
from complex_coordinate_rotation import scan_theta_resonances, compute_resonance_trajectory


def demo_basic_resonance_finding():
    """Example 1: Find resonances at a fixed theta value."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Resonance Finding")
    print("=" * 70)
    
    # Solve with complex scaling at theta=0.3 rad
    result = solve_mabgps_ccr_with_resonances(
        N=100,
        Z=1,
        lambda_shield=0.1,
        theta=0.3,
        resonance_threshold=1e-6
    )
    
    print(f"\nParameters:")
    print(f"  Z = 1 (hydrogen-like)")
    print(f"  λ = 0.1 (shielding parameter)")
    print(f"  θ = {result['theta']:.3f} rad ({np.degrees(result['theta']):.1f}°)")
    print(f"  N = 100 (grid points)")
    
    print(f"\nResults:")
    print(f"  Bound states: {len(result['bound'])}")
    print(f"  Resonances found: {len(result['energies'])}")
    
    if len(result['energies']) > 0:
        print(f"\n  First 5 resonances:")
        print(f"  {'#':<4} {'E_R (a.u.)':<18} {'Γ (a.u.)':<18}")
        print(f"  {'-'*4} {'-'*18} {'-'*18}")
        for i in range(min(5, len(result['energies']))):
            print(f"  {i+1:<4} {result['energies'][i]:<18.6f} {result['widths'][i]:<18.6e}")
    
    return result


def demo_theta_scanning():
    """Example 2: Scan theta to observe resonance emergence."""
    print("\n" + "=" * 70)
    print("DEMO 2: Theta Scanning (Resonance Emergence)")
    print("=" * 70)
    
    # Define theta values to scan
    theta_values = np.linspace(0.05, 0.4, 15)
    
    print(f"\nScanning θ from {theta_values[0]:.3f} to {theta_values[-1]:.3f} rad")
    print(f"Number of points: {len(theta_values)}")
    
    # Scan resonances
    def solve_wrapper(theta, **kwargs):
        E, vecs, r = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.1, theta=theta, return_complex=True
        )
        return E, vecs, r
    
    scan_results = scan_theta_resonances(
        solve_wrapper,
        theta_values,
        Z=1,
        lambda_shield=0.1
    )
    
    # Analyze results
    print(f"\nResonance count vs θ:")
    print(f"  {'θ (rad)':<12} {'θ (deg)':<12} {'# Resonances':<15}")
    print(f"  {'-'*12} {'-'*12} {'-'*15}")
    
    for theta in theta_values:
        if scan_results[theta] is not None:
            n_res = len(scan_results[theta]['energies'])
            print(f"  {theta:<12.4f} {np.degrees(theta):<12.1f} {n_res:<15}")
    
    return scan_results, theta_values


def demo_resonance_trajectory():
    """Example 3: Track individual resonance in complex energy plane."""
    print("\n" + "=" * 70)
    print("DEMO 3: Resonance Trajectory in Complex Energy Plane")
    print("=" * 70)
    
    # Perform theta scan
    theta_values = np.linspace(0.05, 0.4, 20)
    
    def solve_wrapper(theta, **kwargs):
        E, vecs, r = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.1, theta=theta, return_complex=True
        )
        return E, vecs, r
    
    scan_results = scan_theta_resonances(
        solve_wrapper,
        theta_values,
        Z=1,
        lambda_shield=0.1
    )
    
    # Extract trajectory of first resonance
    theta_traj, E_traj, Gamma_traj = compute_resonance_trajectory(
        scan_results, resonance_index=0
    )
    
    print(f"\nFirst resonance trajectory:")
    print(f"  {'θ (rad)':<12} {'E_R (a.u.)':<18} {'Γ (a.u.)':<18}")
    print(f"  {'-'*12} {'-'*18} {'-'*18}")
    
    for i in range(0, len(theta_traj), max(1, len(theta_traj)//5)):
        print(f"  {theta_traj[i]:<12.4f} {E_traj[i]:<18.6f} {Gamma_traj[i]:<18.6e}")
    
    # Plot trajectory
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Real part vs theta
    ax1.plot(theta_traj, E_traj, 'b.-', linewidth=2, markersize=8)
    ax1.set_xlabel('θ (rad)', fontsize=12)
    ax1.set_ylabel('E_R (a.u.)', fontsize=12)
    ax1.set_title('Resonance Energy vs θ', fontsize=13)
    ax1.grid(True, alpha=0.3)
    
    # Width vs theta
    ax2.semilogy(theta_traj, Gamma_traj, 'r.-', linewidth=2, markersize=8)
    ax2.set_xlabel('θ (rad)', fontsize=12)
    ax2.set_ylabel('Γ (a.u.)', fontsize=12)
    ax2.set_title('Resonance Width vs θ', fontsize=13)
    ax2.grid(True, alpha=0.3, which='both')
    
    plt.tight_layout()
    plt.savefig('ccr_resonance_trajectory.png', dpi=150, bbox_inches='tight')
    print(f"\n  Saved: ccr_resonance_trajectory.png")
    
    return theta_traj, E_traj, Gamma_traj


def demo_complex_plane_visualization():
    """Example 4: Visualize eigenvalue spectrum in complex plane."""
    print("\n" + "=" * 70)
    print("DEMO 4: Eigenvalue Spectrum in Complex Energy Plane")
    print("=" * 70)
    
    # Solve at different theta values
    theta_values = [0.0, 0.15, 0.3]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, theta in enumerate(theta_values):
        E, _, _ = solve_mabgps_ccr(
            N=100, Z=1, lambda_shield=0.1, theta=theta, return_complex=True
        )
        
        ax = axes[idx]
        
        # Plot eigenvalues in complex plane
        ax.scatter(np.real(E), np.imag(E), alpha=0.6, s=20)
        
        # Highlight resonances (Im(E) < -1e-6)
        resonance_mask = np.imag(E) < -1e-6
        if np.any(resonance_mask):
            ax.scatter(np.real(E[resonance_mask]), np.imag(E[resonance_mask]),
                      color='red', s=30, label='Resonances', zorder=5)
        
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=0.5)
        ax.set_xlabel('Re(E) (a.u.)', fontsize=11)
        ax.set_ylabel('Im(E) (a.u.)', fontsize=11)
        ax.set_title(f'θ = {theta:.2f} rad ({np.degrees(theta):.0f}°)', fontsize=12)
        ax.grid(True, alpha=0.3)
        if np.any(resonance_mask):
            ax.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig('ccr_complex_plane.png', dpi=150, bbox_inches='tight')
    print(f"\n  Saved: ccr_complex_plane.png")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("COMPLEX COORDINATE ROTATION (CCR) DEMONSTRATION")
    print("=" * 70)
    
    # Demo 1: Basic resonance finding
    result1 = demo_basic_resonance_finding()
    
    # Demo 2: Theta scanning
    scan_results, theta_values = demo_theta_scanning()
    
    # Demo 3: Resonance trajectory
    theta_traj, E_traj, Gamma_traj = demo_resonance_trajectory()
    
    # Demo 4: Complex plane visualization
    demo_complex_plane_visualization()
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - ccr_resonance_trajectory.png")
    print("  - ccr_complex_plane.png")
    print("\nNext steps:")
    print("  1. Examine the generated plots")
    print("  2. Modify parameters (Z, lambda_shield, theta) to explore")
    print("  3. Use solve_mabgps_ccr_with_resonances() in your own code")
    print("  4. See complex_coordinate_rotation.py for API documentation")


if __name__ == "__main__":
    main()
