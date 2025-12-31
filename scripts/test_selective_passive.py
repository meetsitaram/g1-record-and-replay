#!/usr/bin/env python3
"""
Test script to verify selective passive mode.
This demonstrates that only specified motors are set to passive.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from g1_record_replay.core import G1Interface, get_joint_indices, JOINT_NAMES


def main():
    console = Console()
    
    console.print(Panel.fit(
        "[bold cyan]Selective Passive Mode Test[/bold cyan]\n\n"
        "This script demonstrates that set_passive_mode() only affects\n"
        "the specified motors, leaving others unchanged.\n\n"
        "[yellow]Note:[/yellow] This is a READ-ONLY test that shows the command structure.",
        title="🔬 Test",
        border_style="cyan"
    ))
    
    # Show what would happen for different joint groups
    groups = ["arms", "legs", "waist", "all"]
    
    for group in groups:
        indices = get_joint_indices(group)
        
        console.print(f"\n[bold cyan]Joint Group: {group}[/bold cyan]")
        console.print(f"Number of joints: {len(indices)}")
        
        # Create table showing which motors would be affected
        table = Table(title=f"Motors affected by set_passive_mode('{group}')", 
                     show_header=True, header_style="bold cyan")
        table.add_column("Index", style="cyan", width=6)
        table.add_column("Joint Name", style="yellow", width=30)
        table.add_column("Status", style="green", width=20)
        
        # Show motors that WOULD be passive
        for idx in indices:
            table.add_row(
                str(idx),
                JOINT_NAMES[idx],
                "[bold red]PASSIVE[/bold red] (zero torque)"
            )
        
        console.print(table)
        
        # Show motors that WOULD remain active
        other_indices = [i for i in range(29) if i not in indices]
        if other_indices:
            console.print(f"\n[bold green]Motors that remain ACTIVE:[/bold green] {len(other_indices)}")
            active_names = [JOINT_NAMES[i] for i in other_indices[:5]]  # Show first 5
            console.print(f"  Examples: {', '.join(active_names)}...")
        
        console.print("\n" + "─" * 80)
    
    # Explain the key insight
    console.print(Panel.fit(
        "[bold green]✓ KEY INSIGHT:[/bold green]\n\n"
        "When you call [cyan]set_passive_mode(joint_indices=[...])[/cyan],\n"
        "[bold]ONLY those specific motors are affected![/bold]\n\n"
        "• Motors in the list → Set to passive (mode=0, kp=0, kd=0, tau=0)\n"
        "• Motors NOT in the list → [bold green]Unchanged[/bold green] (keep current state)\n\n"
        "This is why recording arms while standing works:\n"
        "  • Arms (15-28) → PASSIVE (free to move)\n"
        "  • Legs (0-11) → ACTIVE (keep robot standing)\n"
        "  • Waist (12-14) → ACTIVE (maintain torso position)",
        title="💡 Understanding",
        border_style="green"
    ))
    
    console.print("\n[bold]To see this in action:[/bold]")
    console.print("  python scripts/record.py --network-interface enp2s0 --joint-group arms")
    console.print("\n[cyan]The robot will stay standing while arms become freely moveable![/cyan]")


if __name__ == '__main__':
    main()

