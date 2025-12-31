#!/usr/bin/env python3
"""Test SDK connection to G1 robot"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from g1_record_replay.core import G1Interface
from rich.console import Console


def test_connection(network_interface=None):
    """Test connection to G1 robot"""
    console = Console()
    
    console.print("[bold cyan]Testing G1 SDK Connection...[/bold cyan]\n")
    
    try:
        # Initialize interface (read-only test)
        console.print("1. Initializing interface (read-only mode)...")
        interface = G1Interface(network_interface, use_motion_switcher=False)
        interface.initialize()
        console.print("[green]✓ Interface initialized[/green]\n")
        
        # Test state reading
        console.print("2. Reading robot state...")
        for i in range(5):
            state = interface.get_joint_state()
            if state is None:
                console.print(f"[yellow]Attempt {i+1}: No state received[/yellow]")
                time.sleep(0.5)
            else:
                console.print(f"[green]✓ State received (attempt {i+1})[/green]")
                console.print(f"   Sample positions: {state.positions[:5]}")
                console.print(f"   Sample velocities: {state.velocities[:5]}")
                break
        else:
            console.print("[red]Failed to receive state after 5 attempts[/red]")
            return False
        
        console.print("\n[bold green]✓ Connection test passed![/bold green]")
        console.print("\nYou can now use:")
        console.print("  - python scripts/calibrate.py --network-interface " + (network_interface or "auto"))
        console.print("  - python scripts/record.py --network-interface " + (network_interface or "auto"))
        console.print("  - python scripts/replay.py --network-interface " + (network_interface or "auto") + " --episode <path>")
        
        # Cleanup
        interface.shutdown()
        return True
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        return False
    except Exception as e:
        console.print(f"\n[bold red]✗ Connection test failed![/bold red]")
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SDK connection to G1 robot")
    parser.add_argument(
        '--network-interface',
        type=str,
        default=None,
        help='Network interface connected to robot (e.g., enp2s0)'
    )
    
    args = parser.parse_args()
    
    success = test_connection(args.network_interface)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

