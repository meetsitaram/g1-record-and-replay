"""Replay Mode - Execute recorded trajectories on the robot"""

import time
import numpy as np
from typing import Optional
import sys
import select

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .core import G1Interface, DataManager, get_joint_indices
from .safety import SafetyChecker


class Replayer:
    """Handles trajectory replay with safety features"""
    
    def __init__(self, interface: G1Interface, data_manager: DataManager,
                 episode_path: str, playback_speed: float = 1.0,
                 transition_duration: float = 3.0):
        """
        Initialize replayer.
        
        Args:
            interface: G1Interface instance
            data_manager: DataManager instance
            episode_path: Path to episode file
            playback_speed: Speed multiplier for playback (0.25 to 2.0)
            transition_duration: Duration for smooth transition to start (seconds)
        """
        self.interface = interface
        self.data_manager = data_manager
        self.episode_path = episode_path
        self.playback_speed = np.clip(playback_speed, 0.25, 2.0)
        self.transition_duration = transition_duration
        self.console = Console()
        
        # Load episode data
        self.console.print(f"[cyan]Loading episode: {episode_path}[/cyan]")
        self.episode_data = self.data_manager.load_episode(episode_path)
        
        self.joint_positions = self.episode_data['joint_positions']
        self.timestamps = self.episode_data['timestamps']
        self.metadata = self.episode_data['metadata']
        
        # Get joint group/indices from metadata
        self.joint_group = self.metadata.get('joint_group', 'all')
        self.joint_indices = self.metadata.get('joint_indices', None)
        if self.joint_indices is None:
            # Fallback if not in metadata
            self.joint_indices = get_joint_indices(self.joint_group)
        
        # Playback state
        self.running = False
        self.paused = False
        self.start_time = None
        self.pause_time = 0.0
        self.accumulated_pause_time = 0.0
        
        # Print episode info
        self._print_episode_info()
    
    def _print_episode_info(self):
        """Print episode information"""
        self.console.print("\n[bold cyan]Episode Information:[/bold cyan]")
        self.console.print(f"  Episode ID: {self.metadata.get('episode_id', 'unknown')}")
        self.console.print(f"  Joint group: {self.joint_group} ({len(self.joint_indices)} joints)")
        self.console.print(f"  Frames: {self.metadata.get('num_frames', 0)}")
        self.console.print(f"  Duration: {self.metadata.get('duration', 0):.2f}s")
        self.console.print(f"  Frequency: {self.metadata.get('frequency', 0):.1f}Hz")
        if 'description' in self.metadata:
            self.console.print(f"  Description: {self.metadata['description']}")
        self.console.print(f"  Playback speed: {self.playback_speed}x")
        self.console.print()
    
    def _check_keyboard_input(self) -> Optional[str]:
        """Check for keyboard input (non-blocking)"""
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.read(1)
            return line.lower()
        return None
    
    def _smooth_transition(self, start_pos: np.ndarray, target_pos: np.ndarray):
        """
        Smoothly transition from current position to target position.
        
        Args:
            start_pos: Starting joint positions (29,)
            target_pos: Target joint positions (29,)
        """
        self.console.print(f"[yellow]Transitioning to start position ({self.transition_duration}s)...[/yellow]")
        
        start_time = time.time()
        
        while time.time() - start_time < self.transition_duration:
            elapsed = time.time() - start_time
            ratio = elapsed / self.transition_duration
            
            # Smooth interpolation using cosine
            smooth_ratio = (1 - np.cos(ratio * np.pi)) / 2
            
            # Interpolate positions
            current_target = start_pos + (target_pos - start_pos) * smooth_ratio
            
            # Send command (only for specified joints)
            self.interface.send_joint_commands(current_target, joint_indices=self.joint_indices)
            
            time.sleep(0.002)  # 500Hz control
        
        # Send final target position
        self.interface.send_joint_commands(target_pos, joint_indices=self.joint_indices)
        self.console.print("[green]Transition complete[/green]")
    
    def _get_target_position(self, playback_time: float) -> Optional[np.ndarray]:
        """
        Get target position at given playback time.
        
        Args:
            playback_time: Time in playback (seconds)
            
        Returns:
            Target joint positions or None if playback finished
        """
        # Find appropriate frame
        if playback_time < 0:
            return self.joint_positions[0]
        
        # Check if playback finished
        if playback_time > self.timestamps[-1]:
            return None
        
        # Find surrounding frames
        idx = np.searchsorted(self.timestamps, playback_time)
        
        if idx == 0:
            return self.joint_positions[0]
        
        if idx >= len(self.timestamps):
            return self.joint_positions[-1]
        
        # Linear interpolation between frames
        t0 = self.timestamps[idx - 1]
        t1 = self.timestamps[idx]
        pos0 = self.joint_positions[idx - 1]
        pos1 = self.joint_positions[idx]
        
        alpha = (playback_time - t0) / (t1 - t0) if t1 > t0 else 0.0
        return pos0 + (pos1 - pos0) * alpha
    
    def run(self, skip_transition: bool = False):
        """
        Run replay mode.
        
        Args:
            skip_transition: If True, start playing from current position without transition
        """
        self.console.print("[bold red]WARNING: Robot will move. Ensure area is clear![/bold red]")
        response = input("Type 'yes' to continue: ")
        if response.lower() != 'yes':
            self.console.print("[yellow]Replay cancelled[/yellow]")
            return
        
        self.console.print("\n[bold green]Starting replay mode...[/bold green]")
        
        # Get current position
        state = self.interface.get_joint_state()
        if state is None:
            self.console.print("[red]Failed to get robot state![/red]")
            return
        
        current_pos = state.positions
        target_pos = self.joint_positions[0]
        
        # Smooth transition to start position (unless skipped)
        if not skip_transition:
            self._smooth_transition(current_pos, target_pos)
        else:
            self.console.print("[yellow]Skipping transition - starting from current position[/yellow]")
        
        self.console.print("[bold cyan]Starting playback...[/bold cyan]")
        self.console.print("[bold]Press 'P' to pause/resume, 'Q' to quit[/bold]\n")
        
        self.running = True
        self.paused = False
        self.start_time = time.time()
        self.accumulated_pause_time = 0.0
        
        # Set terminal to non-blocking mode
        import tty
        import termios
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            tty.setcbreak(sys.stdin.fileno())
            
            total_duration = self.timestamps[-1] / self.playback_speed
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                
                task = progress.add_task("[cyan]Replaying...", total=100)
                
                while self.running:
                    current_time = time.time()
                    
                    # Handle pause
                    if self.paused:
                        if self.pause_time == 0:
                            self.pause_time = current_time
                        time.sleep(0.01)
                        
                        # Check for keyboard input
                        key = self._check_keyboard_input()
                        if key == 'p':
                            self.accumulated_pause_time += current_time - self.pause_time
                            self.pause_time = 0
                            self.paused = False
                            self.console.print("[green]Resumed[/green]")
                        elif key == 'q':
                            self.console.print("\n[yellow]Quitting...[/yellow]")
                            self.running = False
                        continue
                    
                    # Calculate playback time
                    elapsed = current_time - self.start_time - self.accumulated_pause_time
                    playback_time = elapsed * self.playback_speed
                    
                    # Get target position
                    target_pos = self._get_target_position(playback_time)
                    
                    if target_pos is None:
                        # Playback finished
                        self.console.print("\n[bold green]Playback complete![/bold green]")
                        self.running = False
                        break
                    
                    # Send command (only for specified joints)
                    self.interface.send_joint_commands(target_pos, joint_indices=self.joint_indices)
                    
                    # Update progress
                    progress_pct = min(100, (playback_time / self.timestamps[-1]) * 100)
                    frame_idx = int((playback_time / self.timestamps[-1]) * len(self.timestamps))
                    frame_idx = np.clip(frame_idx, 0, len(self.timestamps) - 1)
                    
                    progress.update(
                        task,
                        completed=progress_pct,
                        description=f"[cyan]Replaying... Frame: {frame_idx}/{len(self.timestamps)}"
                    )
                    
                    # Check for keyboard input
                    key = self._check_keyboard_input()
                    if key == 'p':
                        self.paused = True
                        self.console.print("[yellow]Paused[/yellow]")
                    elif key == 'q':
                        self.console.print("\n[yellow]Quitting...[/yellow]")
                        self.running = False
                    
                    time.sleep(0.002)  # 500Hz control
        
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            # Hold final position briefly
            if target_pos is not None:
                for _ in range(100):
                    self.interface.send_joint_commands(target_pos, joint_indices=self.joint_indices)
                    time.sleep(0.002)
            
            self.console.print("\n[bold green]Replay mode ended[/bold green]")


def run_replay(network_interface: Optional[str] = None,
               episode_path: str = None,
               playback_speed: float = 1.0,
               skip_safety: bool = False):
    """
    Run replay mode.
    
    Args:
        network_interface: Network interface name (e.g., 'enp2s0', 'eth0')
        episode_path: Path to episode file
        playback_speed: Speed multiplier for playback
        skip_safety: Skip safety checks (NOT RECOMMENDED - for testing only)
    """
    console = Console()
    
    if not episode_path:
        console.print("[red]Error: Episode path is required[/red]")
        return
    
    # Load episode metadata to show what will be controlled
    try:
        dm = DataManager()
        episode_data = dm.load_episode(episode_path)
        joint_group = episode_data['metadata'].get('joint_group', 'all')
    except Exception as e:
        console.print(f"[red]Error loading episode: {e}[/red]")
        return
    
    # Safety check
    if not skip_safety:
        safety_checker = SafetyChecker()
        if not safety_checker.pre_replay_safety_check(joint_group):
            console.print("[yellow]Replay aborted for safety reasons.[/yellow]")
            return
    else:
        console.print("[bold red]⚠️ SAFETY CHECKS SKIPPED - DANGEROUS! ⚠️[/bold red]")
        time.sleep(2)
    
    try:
        # Initialize interface (needs motion switcher for active control)
        interface = G1Interface(network_interface, use_motion_switcher=True)
        interface.initialize()
        
        # Initialize data manager
        data_manager = DataManager()
        
        # Create replayer
        replayer = Replayer(interface, data_manager, episode_path, playback_speed)
        
        # Run replay
        replayer.run()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
    finally:
        if 'interface' in locals():
            interface.shutdown()

