"""Episode Trimmer - Trim and adjust recorded episodes"""

import numpy as np
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from rich.console import Console
from rich.table import Table

from ..core import DataManager, G1Interface


class EpisodeTrimmer:
    """Handles trimming and editing of recorded episodes"""
    
    def __init__(self, data_manager: DataManager, interface: Optional[G1Interface] = None):
        """
        Initialize episode trimmer.
        
        Args:
            data_manager: DataManager instance
            interface: Optional G1Interface for visual preview (safe playback)
        """
        self.data_manager = data_manager
        self.interface = interface
        self.console = Console()
        
        # Current episode data
        self.episode_path: Optional[Path] = None
        self.episode_data: Optional[dict] = None
        self.joint_positions: Optional[np.ndarray] = None
        self.timestamps: Optional[np.ndarray] = None
        self.joint_velocities: Optional[np.ndarray] = None
        self.metadata: Optional[dict] = None
    
    def load_episode(self, episode_path: str):
        """
        Load an episode for editing.
        
        Args:
            episode_path: Path to the episode file
        """
        self.episode_path = Path(episode_path)
        
        if not self.episode_path.exists():
            raise FileNotFoundError(f"Episode not found: {episode_path}")
        
        self.console.print(f"[cyan]Loading episode: {episode_path}[/cyan]")
        
        # Load episode data
        self.episode_data = self.data_manager.load_episode(str(episode_path))
        
        self.joint_positions = self.episode_data['joint_positions']
        self.timestamps = self.episode_data['timestamps']
        self.joint_velocities = self.episode_data.get('joint_velocities')
        self.metadata = self.episode_data['metadata']
        
        self.console.print(f"[green]✓ Loaded {len(self.timestamps)} frames[/green]")
    
    def preview_episode(self):
        """Display episode statistics and information"""
        if self.episode_data is None:
            self.console.print("[red]No episode loaded[/red]")
            return
        
        self.console.print("\n[bold cyan]Episode Information[/bold cyan]")
        self.console.print(f"  File: {self.episode_path}")
        self.console.print(f"  Episode ID: {self.metadata.get('episode_id', 'unknown')}")
        
        if 'description' in self.metadata:
            self.console.print(f"  Description: {self.metadata['description']}")
        
        self.console.print(f"\n[bold]Data:[/bold]")
        self.console.print(f"  Frames: {len(self.timestamps)}")
        self.console.print(f"  Duration: {self.timestamps[-1]:.2f}s")
        self.console.print(f"  Frequency: {self.metadata.get('frequency', 0):.1f} Hz")
        self.console.print(f"  Joint Group: {self.metadata.get('joint_group', 'all')}")
        
        # Time range
        self.console.print(f"\n[bold]Time Range:[/bold]")
        self.console.print(f"  Start: {self.timestamps[0]:.3f}s")
        self.console.print(f"  End: {self.timestamps[-1]:.3f}s")
        
        # Joint statistics
        self.console.print(f"\n[bold]Joint Positions:[/bold]")
        self.console.print(f"  Shape: {self.joint_positions.shape}")
        self.console.print(f"  Min: {self.joint_positions.min():.3f} rad")
        self.console.print(f"  Max: {self.joint_positions.max():.3f} rad")
        self.console.print(f"  Mean: {self.joint_positions.mean():.3f} rad")
    
    def trim_start(self, num_frames: int, dry_run: bool = False) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Remove initial frames from the episode.
        
        Args:
            num_frames: Number of frames to remove from the start
            dry_run: If True, don't modify data, just return what would be trimmed
            
        Returns:
            Tuple of (new_positions, new_timestamps) if dry_run, else None
        """
        if self.episode_data is None:
            raise ValueError("No episode loaded")
        
        if num_frames <= 0:
            raise ValueError("num_frames must be positive")
        
        if num_frames >= len(self.timestamps):
            raise ValueError(f"Cannot trim {num_frames} frames from {len(self.timestamps)} total frames")
        
        # Trim data
        new_positions = self.joint_positions[num_frames:]
        new_timestamps = self.timestamps[num_frames:]
        new_velocities = self.joint_velocities[num_frames:] if self.joint_velocities is not None else None
        
        # Adjust timestamps to start from 0
        new_timestamps = new_timestamps - new_timestamps[0]
        
        if dry_run:
            self.console.print(f"[yellow]Dry run: Would trim {num_frames} frames from start[/yellow]")
            self.console.print(f"  Original: {len(self.timestamps)} frames, {self.timestamps[-1]:.2f}s")
            self.console.print(f"  New: {len(new_timestamps)} frames, {new_timestamps[-1]:.2f}s")
            return new_positions, new_timestamps
        
        # Update data
        self.joint_positions = new_positions
        self.timestamps = new_timestamps
        if new_velocities is not None:
            self.joint_velocities = new_velocities
        
        self.console.print(f"[green]✓ Trimmed {num_frames} frames from start[/green]")
        return None
    
    def trim_end(self, num_frames: int, dry_run: bool = False) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Remove final frames from the episode.
        
        Args:
            num_frames: Number of frames to remove from the end
            dry_run: If True, don't modify data, just return what would be trimmed
            
        Returns:
            Tuple of (new_positions, new_timestamps) if dry_run, else None
        """
        if self.episode_data is None:
            raise ValueError("No episode loaded")
        
        if num_frames <= 0:
            raise ValueError("num_frames must be positive")
        
        if num_frames >= len(self.timestamps):
            raise ValueError(f"Cannot trim {num_frames} frames from {len(self.timestamps)} total frames")
        
        # Trim data
        new_positions = self.joint_positions[:-num_frames]
        new_timestamps = self.timestamps[:-num_frames]
        new_velocities = self.joint_velocities[:-num_frames] if self.joint_velocities is not None else None
        
        if dry_run:
            self.console.print(f"[yellow]Dry run: Would trim {num_frames} frames from end[/yellow]")
            self.console.print(f"  Original: {len(self.timestamps)} frames, {self.timestamps[-1]:.2f}s")
            self.console.print(f"  New: {len(new_timestamps)} frames, {new_timestamps[-1]:.2f}s")
            return new_positions, new_timestamps
        
        # Update data
        self.joint_positions = new_positions
        self.timestamps = new_timestamps
        if new_velocities is not None:
            self.joint_velocities = new_velocities
        
        self.console.print(f"[green]✓ Trimmed {num_frames} frames from end[/green]")
        return None
    
    def trim_time_range(self, start_time: Optional[float] = None, 
                       end_time: Optional[float] = None,
                       dry_run: bool = False) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Trim episode to a specific time range.
        
        Args:
            start_time: Start time in seconds (None = keep from beginning)
            end_time: End time in seconds (None = keep to end)
            dry_run: If True, don't modify data
            
        Returns:
            Tuple of (new_positions, new_timestamps) if dry_run, else None
        """
        if self.episode_data is None:
            raise ValueError("No episode loaded")
        
        # Find frame indices
        if start_time is None:
            start_idx = 0
        else:
            start_idx = np.searchsorted(self.timestamps, start_time)
        
        if end_time is None:
            end_idx = len(self.timestamps)
        else:
            end_idx = np.searchsorted(self.timestamps, end_time)
        
        if start_idx >= end_idx:
            raise ValueError("Invalid time range: start must be before end")
        
        # Trim data
        new_positions = self.joint_positions[start_idx:end_idx]
        new_timestamps = self.timestamps[start_idx:end_idx]
        new_velocities = self.joint_velocities[start_idx:end_idx] if self.joint_velocities is not None else None
        
        # Adjust timestamps to start from 0
        new_timestamps = new_timestamps - new_timestamps[0]
        
        if dry_run:
            self.console.print(f"[yellow]Dry run: Would trim to time range [{start_time}, {end_time}][/yellow]")
            self.console.print(f"  Original: {len(self.timestamps)} frames, {self.timestamps[-1]:.2f}s")
            self.console.print(f"  New: {len(new_timestamps)} frames, {new_timestamps[-1]:.2f}s")
            return new_positions, new_timestamps
        
        # Update data
        self.joint_positions = new_positions
        self.timestamps = new_timestamps
        if new_velocities is not None:
            self.joint_velocities = new_velocities
        
        self.console.print(f"[green]✓ Trimmed to time range[/green]")
        return None
    
    def create_backup(self, output_path: Optional[Path] = None) -> Path:
        """
        Create a backup of the original episode.
        
        Args:
            output_path: Custom backup path (auto-generated if None)
            
        Returns:
            Path to backup file
        """
        if self.episode_path is None:
            raise ValueError("No episode loaded")
        
        if output_path is None:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{self.episode_path.stem}.backup_{timestamp}.h5"
            output_path = self.episode_path.parent / backup_name
        else:
            output_path = Path(output_path)
        
        # Copy file
        shutil.copy2(self.episode_path, output_path)
        self.console.print(f"[green]✓ Backup created: {output_path}[/green]")
        
        return output_path
    
    def save_trimmed(self, output_path: Optional[str] = None, 
                    backup: bool = True, overwrite: bool = False):
        """
        Save the trimmed episode.
        
        Args:
            output_path: Output file path (overwrites original if None)
            backup: Create backup of original before overwriting
            overwrite: If False and output exists, raise error
        """
        if self.episode_data is None:
            raise ValueError("No episode loaded")
        
        # Determine output path
        if output_path:
            save_path = Path(output_path)
        else:
            save_path = self.episode_path
        
        # Check if overwriting
        if save_path.exists() and not overwrite:
            if save_path == self.episode_path:
                # Overwriting original - backup required
                if backup:
                    self.create_backup()
                else:
                    raise ValueError("Cannot overwrite original without backup. Set backup=True")
            else:
                raise FileExistsError(f"Output file exists: {save_path}. Set overwrite=True to replace.")
        
        # Update metadata
        duration = self.timestamps[-1] - self.timestamps[0] if len(self.timestamps) > 1 else 0.0
        num_frames = len(self.timestamps)
        avg_frequency = num_frames / duration if duration > 0 else 0.0
        
        self.metadata.update({
            'num_frames': num_frames,
            'duration': float(duration),
            'frequency': float(avg_frequency),
            'trimmed': True,
            'trimmed_at': datetime.now().isoformat()
        })
        
        # Save using DataManager
        self.data_manager.save_episode(
            joint_positions=self.joint_positions,
            timestamps=self.timestamps,
            joint_velocities=self.joint_velocities,
            metadata=self.metadata,
            episode_name=save_path.stem
        )
        
        self.console.print(f"[bold green]✓ Trimmed episode saved: {save_path}[/bold green]")
        self.console.print(f"  Frames: {num_frames}, Duration: {duration:.2f}s, Freq: {avg_frequency:.1f}Hz")
    
    def restore_from_backup(self, backup_path: str):
        """
        Restore episode from a backup file.
        
        Args:
            backup_path: Path to backup file
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        if self.episode_path is None:
            raise ValueError("No original episode path set")
        
        # Copy backup to original location
        shutil.copy2(backup_path, self.episode_path)
        
        self.console.print(f"[green]✓ Restored from backup: {backup_path}[/green]")
        
        # Reload episode
        self.load_episode(str(self.episode_path))
    
    def validate_episode(self) -> bool:
        """
        Validate episode integrity after trimming.
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        if self.episode_data is None:
            raise ValueError("No episode loaded")
        
        errors = []
        
        # Check data consistency
        if len(self.timestamps) != len(self.joint_positions):
            errors.append(f"Timestamp length ({len(self.timestamps)}) != positions length ({len(self.joint_positions)})")
        
        if self.joint_velocities is not None:
            if len(self.joint_velocities) != len(self.timestamps):
                errors.append(f"Velocity length ({len(self.joint_velocities)}) != timestamps length ({len(self.timestamps)})")
        
        # Check timestamps are monotonic
        if not np.all(np.diff(self.timestamps) >= 0):
            errors.append("Timestamps are not monotonically increasing")
        
        # Check for NaN or inf values
        if np.any(np.isnan(self.joint_positions)) or np.any(np.isinf(self.joint_positions)):
            errors.append("Joint positions contain NaN or inf values")
        
        # Check minimum frames
        if len(self.timestamps) < 2:
            errors.append("Episode must have at least 2 frames")
        
        if errors:
            raise ValueError("Episode validation failed:\n  " + "\n  ".join(errors))
        
        self.console.print("[green]✓ Episode validation passed[/green]")
        return True
    
    def visual_preview(self, playback_speed: float = 0.5):
        """
        Safely preview the trimmed episode with robot movement.
        
        SAFETY: 
        1. Prompts user to manually position arms close to episode start (passive mode)
        2. Then does minimal smooth transition to exact start position
        3. Plays episode at slow speed
        
        Args:
            playback_speed: Playback speed multiplier (default: 0.5 for safety)
        """
        if self.episode_data is None:
            raise ValueError("No episode loaded")
        
        if self.interface is None:
            raise ValueError("Visual preview requires G1Interface. Initialize trimmer with interface.")
        
        self.console.print("\n[bold yellow]Visual Preview Mode[/bold yellow]")
        self.console.print("[yellow]⚠️  Robot will move. Ensure area is clear![/yellow]")
        self.console.print(f"Playback speed: {playback_speed}x (slower for safety)\n")
        
        # Get episode start position info
        target_start_pos = self.joint_positions[0]
        
        # Get joint indices from metadata
        joint_group = self.metadata.get('joint_group', 'arms')
        from ..core import get_joint_indices, JOINT_NAMES
        joint_indices = self.metadata.get('joint_indices')
        if joint_indices is None:
            joint_indices = get_joint_indices(joint_group)
        
        # SAFETY STEP 1: Show target position and let user manually position arms
        self.console.print("[bold cyan]Step 1: Manual Positioning (SAFE)[/bold cyan]")
        self.console.print("We'll set motors to passive mode so you can manually position the arms.")
        self.console.print("This minimizes the transition distance and gives you full control.\n")
        
        # Show target joint positions for key joints
        self._show_target_position(target_start_pos, joint_indices)
        
        response = input("\nReady to set motors to passive mode for manual positioning? (yes/no): ")
        if response.lower() != 'yes':
            self.console.print("[yellow]Visual preview cancelled[/yellow]")
            return
        
        # Set motors to passive mode for manual positioning
        self.console.print("\n[cyan]Setting motors to passive mode...[/cyan]")
        self.interface.set_passive_mode(joint_indices=joint_indices)
        
        import time
        time.sleep(0.5)  # Give motors time to go passive
        
        self.console.print("[bold green]✓ Motors are now passive - you can freely move them[/bold green]")
        self.console.print("\n[cyan]Instructions:[/cyan]")
        self.console.print("  1. Manually move the arms to match the target position shown above")
        self.console.print("  2. Get as close as you can (doesn't need to be perfect)")
        self.console.print("  3. The system will do a small smooth transition to the exact position")
        self.console.print("  4. Press Enter when arms are positioned\n")
        
        input("Press Enter when arms are positioned and ready for preview: ")
        
        # Get current position after manual positioning
        state = self.interface.get_joint_state()
        if state is None:
            self.console.print("[red]Failed to get robot state![/red]")
            return
        
        current_pos = state.positions
        
        # Calculate weighted distance to target
        distance, details = self._calculate_position_distance(current_pos, target_start_pos, joint_indices)
        
        self.console.print(f"\n[bold cyan]Position Check:[/bold cyan]")
        self.console.print(f"Weighted distance: {distance:.4f} rad")
        
        # Show breakdown by joint category
        self._show_distance_breakdown(details)
        
        # Weighted threshold: 0.5 rad weighted average
        # This means:
        #   - Shoulders: ~16° average acceptable (0.5/3.0 = 0.167 rad)
        #   - Elbows:   ~24° average acceptable (0.5/2.0 = 0.25 rad)
        #   - Wrists:   ~28° average acceptable (0.5/1.0 = 0.5 rad)
        #   - Hands:    ~57° average acceptable (0.5/0.5 = 1.0 rad)
        
        if distance > 0.5:
            self.console.print("\n[yellow]⚠️  Warning: Some joints are far from target position[/yellow]")
            self.console.print("[yellow]   Transition will be larger. Consider repositioning closer.[/yellow]")
            self.console.print("\n[dim]Hint: Focus on repositioning shoulders first (most important)[/dim]")
            response = input("\nContinue anyway? (yes/no): ")
            if response.lower() != 'yes':
                self.console.print("[yellow]Visual preview cancelled[/yellow]")
                return
        else:
            self.console.print("\n[green]✓ Arms are close to target position - transition will be minimal[/green]")
        
        # SAFETY STEP 2: Smooth transition from manual position to exact start
        self.console.print("\n[bold cyan]Step 2: Precise Positioning[/bold cyan]")
        self.console.print("[cyan]Smoothly transitioning to exact episode start position...[/cyan]")
        self._smooth_transition_to_start(current_pos, target_start_pos)
        
        # SAFETY STEP 3: Play through the trimmed episode
        self.console.print("\n[bold cyan]Step 3: Playing Episode[/bold cyan]")
        self.console.print("[cyan]Playing trimmed episode...[/cyan]")
        self._play_episode(playback_speed)
        
        # SAFETY: Hold final position
        final_pos = self.joint_positions[-1]
        self.console.print("[cyan]Holding final position...[/cyan]")
        for _ in range(100):  # Hold for ~0.2s at 500Hz
            self.interface.send_joint_commands(final_pos)
            import time
            time.sleep(0.002)
        
        self.console.print("\n[bold green]✓ Visual preview complete[/bold green]")
        self.console.print("[yellow]Note: Robot is now at episode end position[/yellow]")
    
    def _show_target_position(self, target_pos: np.ndarray, joint_indices: list):
        """
        Show target joint positions for key joints.
        
        Args:
            target_pos: Target joint positions (29,)
            joint_indices: Indices of joints to display
        """
        from rich.table import Table
        from ..core import JOINT_NAMES
        
        self.console.print("\n[bold]Target Position (Episode Start):[/bold]")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Joint", style="cyan", width=30)
        table.add_column("Target (rad)", justify="right", style="green")
        table.add_column("Target (deg)", justify="right", style="yellow")
        table.add_column("Importance", justify="center", style="magenta")
        
        # Show only arm joints or specified joint group
        for idx in joint_indices[:10]:  # Limit to first 10 to avoid clutter
            joint_name = JOINT_NAMES[idx]
            pos_rad = target_pos[idx]
            pos_deg = np.rad2deg(pos_rad)
            weight = self._get_joint_weight(idx)
            
            # Importance indicator
            if weight >= 2.5:
                importance = "⭐⭐⭐"  # Critical
            elif weight >= 2.0:
                importance = "⭐⭐"    # High
            elif weight >= 1.5:
                importance = "⭐"      # Medium
            else:
                importance = "○"      # Low
            
            table.add_row(joint_name, f"{pos_rad:+7.4f}", f"{pos_deg:+7.2f}°", importance)
        
        if len(joint_indices) > 10:
            table.add_row("...", "...", "...", "...")
        
        self.console.print(table)
        self.console.print("\n[dim]Importance: ⭐⭐⭐ Critical (focus here)  ⭐⭐ High  ⭐ Medium  ○ Low[/dim]")
    
    def _show_distance_breakdown(self, details: dict):
        """
        Show distance breakdown by joint category.
        
        Args:
            details: Dictionary with distance info per category
        """
        from rich.table import Table
        
        if not details:
            return
        
        table = Table(show_header=True, header_style="bold cyan", title="Distance Breakdown")
        table.add_column("Joint Type", style="cyan")
        table.add_column("Avg Diff (rad)", justify="right", style="yellow")
        table.add_column("Avg Diff (deg)", justify="right", style="yellow")
        table.add_column("Importance", justify="center", style="magenta")
        table.add_column("Status", justify="center")
        
        # Sort by importance (weight) descending
        sorted_details = sorted(details.items(), key=lambda x: x[1]['weight'], reverse=True)
        
        for cat_name, cat_info in sorted_details:
            avg_rad = cat_info['avg_diff']
            avg_deg = cat_info['avg_deg']
            weight = cat_info['weight']
            count = cat_info['count']
            
            # Importance stars
            if weight >= 2.5:
                importance = "⭐⭐⭐"
            elif weight >= 2.0:
                importance = "⭐⭐"
            elif weight >= 1.5:
                importance = "⭐"
            else:
                importance = "○"
            
            # Status based on weighted threshold
            # Each category has different acceptable thresholds
            threshold = 0.5 / weight  # Inverse relationship
            if avg_rad < threshold * 0.7:
                status = "[green]✓ Excellent[/green]"
            elif avg_rad < threshold:
                status = "[green]✓ Good[/green]"
            elif avg_rad < threshold * 1.5:
                status = "[yellow]△ Fair[/yellow]"
            else:
                status = "[red]✗ Poor[/red]"
            
            display_name = f"{cat_name.title()} ({count})"
            table.add_row(
                display_name,
                f"{avg_rad:.4f}",
                f"{avg_deg:.2f}°",
                importance,
                status
            )
        
        self.console.print(table)
        self.console.print("\n[dim]Status: ✓ Acceptable  △ Borderline  ✗ Needs adjustment[/dim]")
    
    def _get_joint_weight(self, joint_idx: int) -> float:
        """
        Get importance weight for a joint based on its impact on arm movement.
        
        Higher weight = stricter threshold (more important to get right)
        Lower weight = more lenient threshold (less critical)
        
        Args:
            joint_idx: Joint index (0-28)
            
        Returns:
            Weight multiplier for this joint
        """
        from ..core import JOINT_NAMES
        
        joint_name = JOINT_NAMES[joint_idx].lower()
        
        # Shoulder joints: Highest impact (move entire arm)
        if 'shoulder' in joint_name:
            return 3.0  # Strictest - shoulder error multiplied by 3x
        
        # Elbow joints: High impact (move forearm + hand)
        elif 'elbow' in joint_name:
            return 2.0  # Strict - elbow error multiplied by 2x
        
        # Wrist joints: Medium impact (only move hand)
        elif 'wrist' in joint_name:
            return 1.0  # Normal - baseline threshold
        
        # Hand/finger joints: Low impact (very localized)
        elif any(x in joint_name for x in ['thumb', 'index', 'middle', 'ring', 'pinky']):
            return 0.5  # Lenient - can deviate more
        
        # Waist/hip/leg joints: High impact (move entire body/leg)
        elif any(x in joint_name for x in ['waist', 'hip', 'knee', 'ankle']):
            return 2.5  # Very strict
        
        # Default for unknown joints
        else:
            return 1.5  # Slightly strict by default
    
    def _calculate_position_distance(self, current_pos: np.ndarray, 
                                    target_pos: np.ndarray, 
                                    joint_indices: list) -> tuple[float, dict]:
        """
        Calculate weighted distance between current and target positions.
        
        Uses joint-specific weights where shoulders are weighted higher (stricter)
        and wrists/fingers are weighted lower (more lenient).
        
        Args:
            current_pos: Current joint positions (29,)
            target_pos: Target joint positions (29,)
            joint_indices: Indices of joints to consider
            
        Returns:
            Tuple of (weighted_avg_distance, details_dict)
            - weighted_avg_distance: Weighted average difference in radians
            - details_dict: Breakdown by joint category
        """
        from ..core import JOINT_NAMES
        
        weighted_differences = []
        total_weight = 0
        
        # Track by category for detailed feedback
        categories = {
            'shoulder': {'diffs': [], 'weight': 3.0},
            'elbow': {'diffs': [], 'weight': 2.0},
            'wrist': {'diffs': [], 'weight': 1.0},
            'hand': {'diffs': [], 'weight': 0.5},
            'other': {'diffs': [], 'weight': 1.5}
        }
        
        for idx in joint_indices:
            diff = np.abs(current_pos[idx] - target_pos[idx])
            weight = self._get_joint_weight(idx)
            
            weighted_differences.append(diff * weight)
            total_weight += weight
            
            # Categorize for feedback
            joint_name = JOINT_NAMES[idx].lower()
            if 'shoulder' in joint_name:
                categories['shoulder']['diffs'].append(diff)
            elif 'elbow' in joint_name:
                categories['elbow']['diffs'].append(diff)
            elif 'wrist' in joint_name:
                categories['wrist']['diffs'].append(diff)
            elif any(x in joint_name for x in ['thumb', 'index', 'middle', 'ring', 'pinky']):
                categories['hand']['diffs'].append(diff)
            else:
                categories['other']['diffs'].append(diff)
        
        # Weighted average
        weighted_avg = sum(weighted_differences) / total_weight if total_weight > 0 else 0
        
        # Calculate averages per category for detailed feedback
        details = {}
        for cat_name, cat_data in categories.items():
            if cat_data['diffs']:
                avg_diff = np.mean(cat_data['diffs'])
                details[cat_name] = {
                    'avg_diff': avg_diff,
                    'avg_deg': np.rad2deg(avg_diff),
                    'weight': cat_data['weight'],
                    'count': len(cat_data['diffs'])
                }
        
        return weighted_avg, details
    
    def _smooth_transition_to_start(self, current_pos: np.ndarray, target_pos: np.ndarray, 
                                    duration: float = 2.0):
        """
        Smoothly transition from current position to target position.
        
        Args:
            current_pos: Current joint positions (29,)
            target_pos: Target joint positions (29,)
            duration: Transition duration in seconds
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            ratio = elapsed / duration
            
            # Smooth interpolation using cosine
            smooth_ratio = (1 - np.cos(ratio * np.pi)) / 2
            
            # Interpolate positions
            interpolated_pos = current_pos + (target_pos - current_pos) * smooth_ratio
            
            # Send command
            self.interface.send_joint_commands(interpolated_pos)
            
            time.sleep(0.002)  # 500Hz control
        
        # Send final target position
        self.interface.send_joint_commands(target_pos)
    
    def _play_episode(self, playback_speed: float):
        """
        Play through the loaded episode.
        
        Args:
            playback_speed: Playback speed multiplier
        """
        import time
        
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            playback_time = elapsed * playback_speed
            
            # Find current frame
            if playback_time > self.timestamps[-1]:
                break  # Playback finished
            
            # Find frame index using binary search
            frame_idx = np.searchsorted(self.timestamps, playback_time)
            
            if frame_idx >= len(self.timestamps):
                frame_idx = len(self.timestamps) - 1
            
            # Get target position (with interpolation between frames)
            if frame_idx == 0:
                target_pos = self.joint_positions[0]
            else:
                # Linear interpolation between frames
                t0 = self.timestamps[frame_idx - 1]
                t1 = self.timestamps[frame_idx]
                pos0 = self.joint_positions[frame_idx - 1]
                pos1 = self.joint_positions[frame_idx]
                
                alpha = (playback_time - t0) / (t1 - t0) if t1 > t0 else 0.0
                target_pos = pos0 + (pos1 - pos0) * alpha
            
            # Send command
            self.interface.send_joint_commands(target_pos)
            
            time.sleep(0.002)  # 500Hz control

