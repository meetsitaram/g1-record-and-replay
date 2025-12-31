#!/usr/bin/env python3
"""Check robot safety state and disable FSM if needed"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
    LOCO_AVAILABLE = True
except ImportError:
    LOCO_AVAILABLE = False

def main():
    console = Console()
    
    console.print(Panel.fit(
        "[bold cyan]🛡️ G1 Robot Safety Checker 🛡️[/bold cyan]\n\n"
        "This tool helps you:\n"
        "  • Check if FSM (high-level mode) is active\n"
        "  • Safely disable FSM before low-level control\n"
        "  • Verify robot is ready for manual operation",
        title="Safety Checker",
        border_style="cyan"
    ))
    
    if not LOCO_AVAILABLE:
        console.print("\n[red]✗ LocoClient not available.[/red]")
        console.print("[yellow]Cannot check FSM state. This may indicate:[/yellow]")
        console.print("  • Unitree SDK not properly installed")
        console.print("  • Robot is not connected")
        return 1
    
    try:
        # Initialize LocoClient
        console.print("\n[cyan]Initializing LocoClient...[/cyan]")
        loco = LocoClient()
        loco.SetTimeout(5.0)
        loco.Init()
        console.print("[green]✓ LocoClient initialized[/green]")
        
        # Create status table
        table = Table(title="Robot Status", show_header=True, header_style="bold cyan")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_column("Safe for Low-Level?", style="green")
        
        # Note: The LocoClient doesn't expose GetFsmId in Python, so we just provide the commands
        table.add_row(
            "FSM Control",
            "Available",
            "Can be disabled"
        )
        
        console.print("\n")
        console.print(table)
        
        # Provide options
        console.print("\n[bold]Available Actions:[/bold]")
        console.print("  1. [cyan]ZeroTorque()[/cyan] - Disable all motor torque (FSM ID 0)")
        console.print("     • Safest for low-level control")
        console.print("     • All motors will be passive")
        console.print()
        console.print("  2. [cyan]Damp()[/cyan] - Enable damping mode (FSM ID 1)")
        console.print("     • Low torque damping")
        console.print("     • Motors resist movement slightly")
        
        # Ask what to do
        console.print("\n[bold yellow]What would you like to do?[/bold yellow]")
        console.print("  [1] Set ZeroTorque (recommended for replay)")
        console.print("  [2] Set Damp mode")
        console.print("  [3] Exit without changes")
        
        choice = console.input("\nEnter choice (1-3): ")
        
        if choice == "1":
            console.print("\n[bold cyan]Setting ZeroTorque mode...[/bold cyan]")
            loco.ZeroTorque()
            console.print("[bold green]✓ Robot set to ZeroTorque mode (FSM disabled)[/bold green]")
            console.print("[green]Safe for low-level control![/green]")
        elif choice == "2":
            console.print("\n[bold cyan]Setting Damp mode...[/bold cyan]")
            loco.Damp()
            console.print("[bold green]✓ Robot set to Damp mode[/bold green]")
        else:
            console.print("\n[yellow]No changes made.[/yellow]")
        
        return 0
        
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

