"""Calibration Mode - Discover and save joint limits"""

import time
import numpy as np
from typing import Dict, List, Optional
import sys
import select

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

from .core import G1Interface, JOINT_NAMES, DataManager


class Calibrator:
    """Handles joint calibration with live display"""
    
    def __init__(self, interface: G1Interface, data_manager: DataManager, joint_group: str = "all"):
        """
        Initialize calibrator.
        
        Args:
            interface: G1Interface instance
            data_manager: DataManager instance
            joint_group: Which joints to calibrate ('all', 'arms', 'legs', 'waist')
        """
        self.interface = interface
        self.data_manager = data_manager
        self.console = Console()
        
        # Joint groups (indices)
        self.joint_groups = {
            "legs": list(range(0, 12)),  # indices 0-11
            "waist": list(range(12, 15)),  # indices 12-14
            "arms": list(range(15, 29)),  # indices 15-28
            "all": list(range(29))
        }
        
        if joint_group not in self.joint_groups:
            raise ValueError(f"Invalid joint group: {joint_group}. Choose from {list(self.joint_groups.keys())}")
        
        self.active_joints = self.joint_groups[joint_group]
        self.joint_group = joint_group
        
        # Calibration data
        self.min_positions = np.full(29, np.inf)
        self.max_positions = np.full(29, -np.inf)
        self.current_positions = np.zeros(29)
        
        self.running = False
        self.start_time = None
    
    def reset_limits(self):
        """Reset min/max limits"""
        self.min_positions = np.full(29, np.inf)
        self.max_positions = np.full(29, -np.inf)
        self.console.print("[yellow]Limits reset[/yellow]")
    
    def _update_calibration(self):
        """Update calibration data from current state"""
        state = self.interface.get_joint_state()
        if state is None:
            return
        
        self.current_positions = state.positions
        
        # Update min/max for active joints
        for idx in self.active_joints:
            pos = state.positions[idx]
            if pos < self.min_positions[idx]:
                self.min_positions[idx] = pos
            if pos > self.max_positions[idx]:
                self.max_positions[idx] = pos
    
    def _create_display_table(self) -> Table:
        """Create display table for calibration data"""
        table = Table(title=f"Joint Calibration - {self.joint_group.upper()}", show_header=True)
        
        table.add_column("Index", justify="right", style="cyan")
        table.add_column("Joint Name", style="magenta")
        table.add_column("Current", justify="right", style="white")
        table.add_column("Min", justify="right", style="green")
        table.add_column("Max", justify="right", style="red")
        table.add_column("Range", justify="right", style="yellow")
        
        for idx in self.active_joints:
            joint_name = JOINT_NAMES[idx]
            current = self.current_positions[idx]
            min_val = self.min_positions[idx]
            max_val = self.max_positions[idx]
            
            # Calculate range
            if np.isfinite(min_val) and np.isfinite(max_val):
                range_val = max_val - min_val
                range_str = f"{range_val:.3f}"
            else:
                range_str = "---"
            
            # Format values
            current_str = f"{current:.3f}"
            min_str = f"{min_val:.3f}" if np.isfinite(min_val) else "---"
            max_str = f"{max_val:.3f}" if np.isfinite(max_val) else "---"
            
            table.add_row(
                str(idx),
                joint_name,
                current_str,
                min_str,
                max_str,
                range_str
            )
        
        return table
    
    def _create_display_panel(self) -> Panel:
        """Create display panel with table and instructions"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Create layout
        table = self._create_display_table()
        
        instructions = (
            "[bold cyan]Instructions:[/bold cyan]\n"
            "• Manually move joints to their maximum limits\n"
            "• Press [bold]R[/bold] to reset min/max values\n"
            "• Press [bold]S[/bold] to save calibration and exit\n"
            "• Press [bold]Q[/bold] to quit without saving\n\n"
            f"[dim]Elapsed time: {elapsed:.1f}s[/dim]"
        )
        
        return Panel(
            f"{table}\n\n{instructions}",
            title="[bold]G1 Calibration Mode[/bold]",
            border_style="blue"
        )
    
    def _check_keyboard_input(self) -> Optional[str]:
        """Check for keyboard input (non-blocking)"""
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.read(1)
            return line.lower()
        return None
    
    def run(self):
        """Run calibration mode"""
        self.console.print("[bold green]Starting calibration mode...[/bold green]")
        self.console.print("[yellow]Move joints to their limits. The system will record min/max positions.[/yellow]\n")
        
        self.running = True
        self.start_time = time.time()
        
        # Set terminal to non-blocking mode
        import tty
        import termios
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            tty.setcbreak(sys.stdin.fileno())
            
            with Live(self._create_display_panel(), refresh_per_second=10, console=self.console) as live:
                while self.running:
                    # Update calibration data
                    self._update_calibration()
                    
                    # Update display
                    live.update(self._create_display_panel())
                    
                    # Check for keyboard input
                    key = self._check_keyboard_input()
                    if key == 'r':
                        self.reset_limits()
                    elif key == 's':
                        self._save_calibration()
                        self.running = False
                    elif key == 'q':
                        self.console.print("[yellow]Quitting without saving...[/yellow]")
                        self.running = False
                    
                    time.sleep(0.05)  # 20Hz update
        
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.console.print("\n[bold green]Calibration mode ended[/bold green]")
    
    def _save_calibration(self):
        """Save calibration data to file"""
        self.console.print("\n[bold cyan]Saving calibration...[/bold cyan]")
        
        # Prepare calibration data
        joint_limits = {}
        
        for idx in self.active_joints:
            joint_name = JOINT_NAMES[idx]
            
            if np.isfinite(self.min_positions[idx]) and np.isfinite(self.max_positions[idx]):
                joint_limits[joint_name] = {
                    "min": float(self.min_positions[idx]),
                    "max": float(self.max_positions[idx]),
                    "index": idx,
                    "name": joint_name
                }
        
        if not joint_limits:
            self.console.print("[red]No calibration data to save![/red]")
            return
        
        # Load existing calibration and merge
        existing = self.data_manager.load_calibration()
        if existing and 'joints' in existing:
            existing['joints'].update(joint_limits)
            joint_limits = existing['joints']
        
        # Save to file
        self.data_manager.save_calibration(joint_limits)
        
        self.console.print(f"[bold green]✓ Calibration saved for {len(joint_limits)} joints[/bold green]")


def run_calibration(network_interface: Optional[str] = None, joint_group: str = "all"):
    """
    Run calibration mode.
    
    Args:
        network_interface: Network interface name (e.g., 'enp2s0', 'eth0')
        joint_group: Which joints to calibrate ('all', 'arms', 'legs', 'waist')
    """
    console = Console()
    
    try:
        # Initialize interface (read-only, no motion switcher needed)
        interface = G1Interface(network_interface, use_motion_switcher=False)
        interface.initialize()
        
        # Initialize data manager
        data_manager = DataManager()
        
        # Create calibrator
        calibrator = Calibrator(interface, data_manager, joint_group)
        
        # Run calibration
        calibrator.run()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
    finally:
        if 'interface' in locals():
            interface.shutdown()

