"""Record Mode - Capture joint trajectories with motors in passive mode"""

import time
import numpy as np
from typing import Optional, List
import sys
import select

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from .core import G1Interface, DataManager, get_joint_indices, JOINT_NAMES
from .safety import SafetyChecker


class Recorder:
    """Handles trajectory recording with passive motors"""
    
    def __init__(self, interface: G1Interface, data_manager: DataManager, 
                 frequency: float = 50.0, episode_name: Optional[str] = None,
                 joint_group: str = "all", show_positions: bool = False):
        """
        Initialize recorder.
        
        Args:
            interface: G1Interface instance
            data_manager: DataManager instance
            frequency: Recording frequency in Hz
            episode_name: Name/description for the episode
            joint_group: Which joints to record ('all', 'arms', 'legs', 'waist')
            show_positions: Whether to display joint positions in real-time
        """
        self.interface = interface
        self.data_manager = data_manager
        self.frequency = frequency
        self.episode_name = episode_name
        self.joint_group = joint_group
        self.joint_indices = get_joint_indices(joint_group)
        self.show_positions = show_positions
        self.console = Console()
        
        # Recording data
        self.joint_positions: List[np.ndarray] = []
        self.joint_velocities: List[np.ndarray] = []
        self.timestamps: List[float] = []
        
        self.running = False
        self.start_time = None
        self.last_position_print = 0
    
    def _check_keyboard_input(self) -> Optional[str]:
        """Check for keyboard input (non-blocking)"""
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.read(1)
            return line.lower()
        return None
    
    def _record_frame(self):
        """Record a single frame and maintain passive mode"""
        state = self.interface.get_joint_state()
        if state is None:
            return
        
        # Continuously send passive command to keep motors completely free
        # This reduces any residual resistance by ensuring zero torque at each cycle
        self.interface.set_passive_mode(joint_indices=self.joint_indices, continuous=True)
        
        self.joint_positions.append(state.positions.copy())
        self.joint_velocities.append(state.velocities.copy())
        self.timestamps.append(time.time() - self.start_time)
    
    def _print_joint_positions(self, positions: np.ndarray):
        """Print current joint positions in a nice format"""
        current_time = time.time()
        
        # Only print every 0.5 seconds to avoid flooding the terminal
        if current_time - self.last_position_print < 0.5:
            return
        
        self.last_position_print = current_time
        
        # Create table for joint positions
        table = Table(title="Current Joint Positions", show_header=True, header_style="bold cyan")
        table.add_column("Joint Name", style="cyan", width=30)
        table.add_column("Position (rad)", justify="right", style="green")
        table.add_column("Position (deg)", justify="right", style="yellow")
        
        # Display only the joints in the selected group
        for idx in self.joint_indices:
            joint_name = JOINT_NAMES[idx]
            pos_rad = positions[idx]
            pos_deg = np.rad2deg(pos_rad)
            table.add_row(joint_name, f"{pos_rad:+7.4f}", f"{pos_deg:+7.2f}°")
        
        # Clear previous output and print new table
        self.console.clear()
        self.console.print(table)
        self.console.print(f"\n[bold cyan]Recording... Frames: {len(self.timestamps)}, "
                          f"Duration: {time.time() - self.start_time:.1f}s[/bold cyan]")
        self.console.print("[bold]Press 'S' to stop and save, 'C' to cancel[/bold]\n")
    
    def run(self):
        """Run recording mode"""
        self.console.print("[bold green]Starting recording mode...[/bold green]")
        self.console.print(f"[cyan]Joint group: {self.joint_group} ({len(self.joint_indices)} joints)[/cyan]")
        self.console.print("[yellow]Setting motors to passive mode...[/yellow]")
        
        # Set motors to passive mode (only specified joints)
        self.interface.set_passive_mode(joint_indices=self.joint_indices)
        time.sleep(0.5)  # Give time for motors to disable
        
        self.console.print(f"[bold cyan]Motors ({self.joint_group}) are now passive. You can freely move them.[/bold cyan]")
        self.console.print("[bold]Press 'S' to stop and save, 'C' to cancel[/bold]\n")
        
        self.running = True
        self.start_time = time.time()
        
        # Set terminal to non-blocking mode
        import tty
        import termios
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            tty.setcbreak(sys.stdin.fileno())
            
            # Use different display modes based on show_positions flag
            if self.show_positions:
                # Simple mode without progress bar - show joint positions
                interval = 1.0 / self.frequency
                next_frame_time = time.time()
                
                while self.running:
                    current_time = time.time()
                    
                    # Record frame at specified frequency
                    if current_time >= next_frame_time:
                        self._record_frame()
                        next_frame_time += interval
                        
                        # Print joint positions
                        if len(self.joint_positions) > 0:
                            self._print_joint_positions(self.joint_positions[-1])
                    
                    # Check for keyboard input
                    key = self._check_keyboard_input()
                    if key == 's':
                        self.console.print("\n[bold green]Stopping and saving...[/bold green]")
                        self._save_recording()
                        self.running = False
                    elif key == 'c':
                        self.console.print("\n[yellow]Canceling without saving...[/yellow]")
                        self.running = False
                    
                    # Small sleep to prevent busy waiting
                    time.sleep(0.001)
            else:
                # Progress bar mode (default)
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=self.console
                ) as progress:
                    
                    # Create infinite progress task
                    task = progress.add_task("[cyan]Recording...", total=None)
                    
                    interval = 1.0 / self.frequency
                    next_frame_time = time.time()
                    
                    while self.running:
                        current_time = time.time()
                        
                        # Record frame at specified frequency
                        if current_time >= next_frame_time:
                            self._record_frame()
                            next_frame_time += interval
                            
                            # Update progress display
                            elapsed = time.time() - self.start_time
                            num_frames = len(self.timestamps)
                            actual_freq = num_frames / elapsed if elapsed > 0 else 0
                            
                            progress.update(
                                task, 
                                description=f"[cyan]Recording... Frames: {num_frames}, "
                                           f"Duration: {elapsed:.1f}s, "
                                           f"Freq: {actual_freq:.1f}Hz"
                            )
                        
                        # Check for keyboard input
                        key = self._check_keyboard_input()
                        if key == 's':
                            self.console.print("\n[bold green]Stopping and saving...[/bold green]")
                            self._save_recording()
                            self.running = False
                        elif key == 'c':
                            self.console.print("\n[yellow]Canceling without saving...[/yellow]")
                            self.running = False
                        
                        # Small sleep to prevent busy waiting
                        time.sleep(0.001)
        
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.console.print("\n[bold green]Recording mode ended[/bold green]")
    
    def _save_recording(self):
        """Save recorded data to file"""
        if len(self.timestamps) == 0:
            self.console.print("[red]No data recorded![/red]")
            return
        
        self.console.print("\n[bold cyan]Saving episode...[/bold cyan]")
        
        # Convert lists to arrays
        joint_positions = np.array(self.joint_positions)
        joint_velocities = np.array(self.joint_velocities)
        timestamps = np.array(self.timestamps)
        
        # Prepare metadata
        metadata = {
            'joint_group': self.joint_group,
            'joint_indices': self.joint_indices
        }
        if self.episode_name:
            metadata['description'] = self.episode_name
        
        # Save episode
        try:
            filepath = self.data_manager.save_episode(
                joint_positions=joint_positions,
                timestamps=timestamps,
                joint_velocities=joint_velocities,
                metadata=metadata,
                episode_name=self.episode_name
            )
            self.console.print(f"[bold green]✓ Episode saved: {filepath}[/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]Error saving episode: {e}[/bold red]")
            import traceback
            traceback.print_exc()


def run_recording(network_interface: Optional[str] = None, 
                  frequency: float = 50.0,
                  episode_name: Optional[str] = None,
                  joint_group: str = "arms",
                  show_positions: bool = False,
                  skip_safety: bool = False):
    """
    Run recording mode.
    
    Args:
        network_interface: Network interface name (e.g., 'enp2s0', 'eth0')
        frequency: Recording frequency in Hz
        episode_name: Name/description for the episode
        joint_group: Which joints to record ('all', 'arms', 'legs', 'waist')
        show_positions: Whether to display joint positions in real-time
        skip_safety: Skip safety checks (NOT RECOMMENDED - for testing only)
    """
    console = Console()
    
    # Safety check
    if not skip_safety:
        safety_checker = SafetyChecker()
        if not safety_checker.pre_record_safety_check(joint_group):
            console.print("[yellow]Recording cancelled.[/yellow]")
            return
    
    try:
        # Initialize interface (needs motion switcher to set passive mode)
        interface = G1Interface(network_interface, use_motion_switcher=True)
        interface.initialize()
        
        # Initialize data manager
        data_manager = DataManager()
        
        # Create recorder
        recorder = Recorder(interface, data_manager, frequency, episode_name, 
                          joint_group, show_positions)
        
        # Run recording
        recorder.run()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
    finally:
        if 'interface' in locals():
            interface.shutdown()

