"""Music Replayer - Play musical sequences with proper timing"""

import time
import threading
import numpy as np
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel

from ..core import G1Interface, DataManager
from ..replay import Replayer
from .music_config import MusicConfig


class NoteAction:
    """Represents a single note action with timing"""
    
    def __init__(self, note: str, hand: str, duration: str, duration_seconds: float):
        """
        Initialize note action.
        
        Args:
            note: Note name (e.g., 'C1', 'D2') or 'rest'
            hand: Hand to use ('left' or 'right')
            duration: Duration type (e.g., 'quarter', 'half')
            duration_seconds: Duration in seconds
        """
        self.note = note
        self.hand = hand
        self.duration = duration
        self.duration_seconds = duration_seconds
        self.is_rest = (note.lower() == "rest")
    
    def __repr__(self):
        return f"NoteAction({self.note}:{self.hand}:{self.duration})"


class ChordAction:
    """Represents simultaneous notes (chord)"""
    
    def __init__(self, notes: List[NoteAction]):
        """
        Initialize chord action.
        
        Args:
            notes: List of NoteAction objects to play simultaneously
        """
        self.notes = notes
        # Duration of chord is the longest note
        self.duration_seconds = max(n.duration_seconds for n in notes)
    
    def __repr__(self):
        note_strs = [f"{n.note}:{n.hand}" for n in self.notes]
        return f"ChordAction({';'.join(note_strs)})"


class MusicReplayer:
    """Handles music playback with proper timing and note durations"""
    
    def __init__(self, config: MusicConfig, interface: G1Interface, 
                 data_manager: DataManager):
        """
        Initialize music replayer.
        
        Args:
            config: MusicConfig instance
            interface: G1Interface instance
            data_manager: DataManager instance
        """
        self.config = config
        self.interface = interface
        self.data_manager = data_manager
        self.console = Console()
        
        # Playback state
        self.playing = False
        self.paused = False
    
    def parse_sequence(self, sequence_str: str) -> List[ChordAction]:
        """
        Parse note sequence string into structured actions.
        
        Format: "C1:left:quarter -> D1:right:half -> E1:left:quarter;G1:right:quarter"
        
        Components:
            - '->' separates sequential notes/chords
            - ';' separates simultaneous notes within a chord
            - 'note:hand:duration' specifies each note
            - 'rest:none:duration' creates a pause
        
        Args:
            sequence_str: Note sequence string
            
        Returns:
            List of ChordAction objects
        """
        actions = []
        
        # Split by '->' for sequential notes
        sequential_groups = sequence_str.split('->')
        
        for group_idx, group in enumerate(sequential_groups):
            group = group.strip()
            
            if not group:
                continue
            
            # Split by ';' for simultaneous notes (chords)
            simultaneous_notes = group.split(';')
            
            note_actions = []
            for note_spec in simultaneous_notes:
                note_spec = note_spec.strip()
                
                if not note_spec:
                    continue
                
                parts = note_spec.split(':')
                
                if len(parts) != 3:
                    raise ValueError(
                        f"Invalid note format: '{note_spec}'. "
                        f"Expected 'note:hand:duration' (e.g., 'C1:left:quarter')"
                    )
                
                note_name, hand, duration = parts
                note_name = note_name.strip()
                hand = hand.strip()
                duration = duration.strip()
                
                # Validate note (skip for rests)
                if note_name.lower() != "rest":
                    if note_name not in self.config.notes:
                        raise ValueError(
                            f"Unknown note: '{note_name}'. "
                            f"Available notes: {', '.join(sorted(self.config.notes.keys()))}"
                        )
                    
                    # Check if episode exists
                    note_info = self.config.notes[note_name]
                    if not Path(note_info['episode_path']).exists():
                        raise ValueError(
                            f"Episode not found for note '{note_name}': {note_info['episode_path']}"
                        )
                    
                    # Validate hand matches configuration
                    if hand not in ['left', 'right']:
                        raise ValueError(f"Invalid hand: '{hand}'. Must be 'left' or 'right'")
                    
                    if hand != note_info['hand']:
                        raise ValueError(
                            f"Hand mismatch for note '{note_name}': "
                            f"configured as '{note_info['hand']}', but sequence uses '{hand}'"
                        )
                
                # Validate duration
                if duration not in self.config.note_durations:
                    raise ValueError(
                        f"Unknown duration: '{duration}'. "
                        f"Available: {', '.join(sorted(self.config.note_durations.keys()))}"
                    )
                
                duration_seconds = self.config.note_durations[duration]
                
                note_actions.append(NoteAction(note_name, hand, duration, duration_seconds))
            
            if note_actions:
                actions.append(ChordAction(note_actions))
        
        if not actions:
            raise ValueError("No valid notes found in sequence")
        
        return actions
    
    def validate_sequence(self, actions: List[ChordAction]):
        """
        Validate that all notes in sequence are playable.
        
        Args:
            actions: List of ChordAction objects
        """
        for action_idx, action in enumerate(actions):
            for note in action.notes:
                if note.is_rest:
                    continue
                
                # Check episode exists
                note_info = self.config.notes[note.note]
                episode_path = Path(note_info['episode_path'])
                
                if not episode_path.exists():
                    raise ValueError(
                        f"Action {action_idx + 1}: Episode missing for note '{note.note}'"
                    )
                
                # Check if recorded
                if not note_info['recorded_at']:
                    raise ValueError(
                        f"Action {action_idx + 1}: Note '{note.note}' not recorded yet"
                    )
        
        self.console.print("[green]✓ Sequence validation passed[/green]")
    
    def play_song(self, sequence_str: str, playback_speed: float = 1.0,
                  tempo_multiplier: float = 1.0, skip_init: bool = False,
                  skip_final: bool = False, note_speed: Optional[float] = None):
        """
        Play musical sequence with proper timing.
        
        Args:
            sequence_str: Note sequence string (format: "note:hand:duration -> ...")
            playback_speed: Speed of episode playback for init/final positions
            tempo_multiplier: Speed of timing between notes (affects rhythm)
            skip_init: Skip initial position transition
            skip_final: Skip final position transition
            note_speed: Speed multiplier for note playback only (if None, uses playback_speed)
        """
        # If note_speed not specified, use playback_speed for everything
        if note_speed is None:
            note_speed = playback_speed
        
        self.console.print(Panel.fit(
            f"[bold cyan]🎵 Music Playback[/bold cyan]\n"
            f"Instrument: {self.config.instrument_name}\n"
            f"Tempo: {self.config.tempo_bpm} BPM (×{tempo_multiplier})\n"
            f"Init/Final Speed: {playback_speed}×\n"
            f"Note Speed: {note_speed}×",
            border_style="cyan"
        ))
        
        # Parse and validate sequence
        try:
            actions = self.parse_sequence(sequence_str)
            self.console.print(f"[cyan]Parsed {len(actions)} actions from sequence[/cyan]")
            
            self.validate_sequence(actions)
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return
        
        # Display sequence preview
        self._print_sequence_preview(actions, tempo_multiplier)
        
        # Confirm before playing
        response = input("\n[SAFETY] Robot will move. Type 'yes' to continue: ")
        if response.lower() != 'yes':
            self.console.print("[yellow]Playback cancelled[/yellow]")
            return
        
        try:
            self.playing = True
            
            # Move to init position (transition to ready position, not play the whole episode)
            if not skip_init and self.config.init_position_episode:
                self.console.print("\n[cyan]Moving to initial position...[/cyan]")
                self._transition_to_position(self.config.init_position_episode, use_end=True)
                time.sleep(0.5)  # Brief pause after init
            
            # Play sequence (use note_speed for notes)
            self._play_sequence(actions, note_speed, tempo_multiplier)
            
            # Move to final position (transition to rest position, not play the whole episode)
            if not skip_final and self.config.final_position_episode:
                time.sleep(0.5)  # Brief pause before final
                self.console.print("\n[cyan]Returning to final position...[/cyan]")
                self._transition_to_position(self.config.final_position_episode, use_end=True)
            
            self.console.print("\n[bold green]✓ Playback complete![/bold green]")
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Playback interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error during playback: {e}[/red]")
            import traceback
            traceback.print_exc()
        finally:
            self.playing = False
    
    def _play_sequence(self, actions: List[ChordAction], playback_speed: float,
                      tempo_multiplier: float):
        """Play the sequence of actions"""
        total_duration = sum(a.duration_seconds for a in actions) * tempo_multiplier
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("[cyan]Playing music...", total=len(actions))
            
            for i, chord_action in enumerate(actions):
                if not self.playing:
                    break
                
                # Update progress
                progress.update(
                    task,
                    completed=i,
                    description=f"[cyan]Action {i+1}/{len(actions)}"
                )
                
                # Play the action (single note or chord)
                if len(chord_action.notes) == 1:
                    # Single note
                    note_action = chord_action.notes[0]
                    self._play_note_action(note_action, playback_speed)
                else:
                    # Chord (simultaneous notes)
                    self._play_chord(chord_action, playback_speed)
                
                # Wait based on note duration
                wait_time = chord_action.duration_seconds * tempo_multiplier
                
                # Display what was just played
                note_info = self._format_action_info(chord_action)
                self.console.print(f"  [green]Played:[/green] {note_info} [dim]({wait_time:.2f}s)[/dim]")
                
                # Wait before next note (unless it's the last one)
                if i < len(actions) - 1:
                    time.sleep(wait_time)
            
            progress.update(task, completed=len(actions))
    
    def _play_note_action(self, note_action: NoteAction, playback_speed: float):
        """Play a single note"""
        if note_action.is_rest:
            # Rest - just wait (handled by caller)
            return
        
        note_info = self.config.notes[note_action.note]
        episode_path = note_info['episode_path']
        
        # Skip transition for notes - they should start from current position (ready position)
        self._play_episode(episode_path, playback_speed, skip_transition=True)
    
    def _play_chord(self, chord_action: ChordAction, playback_speed: float):
        """Play simultaneous notes using threading"""
        threads = []
        exceptions = []
        
        def play_note_thread(note_action: NoteAction):
            try:
                if not note_action.is_rest:
                    self._play_note_action(note_action, playback_speed)
            except Exception as e:
                exceptions.append((note_action, e))
        
        # Start all threads simultaneously
        for note_action in chord_action.notes:
            thread = threading.Thread(target=play_note_thread, args=(note_action,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Report any exceptions
        if exceptions:
            for note_action, exc in exceptions:
                self.console.print(f"[red]Error playing {note_action.note}: {exc}[/red]")
    
    def _transition_to_position(self, episode_path: str, use_end: bool = True, 
                               transition_duration: float = 3.0):
        """
        Smoothly transition to a position from an episode (start or end frame).
        
        Args:
            episode_path: Path to episode file
            use_end: If True, transition to end position; if False, to start position
            transition_duration: Duration of transition in seconds
        """
        # Load episode to get target position
        episode_data = self.data_manager.load_episode(episode_path)
        
        if use_end:
            target_pos = episode_data['joint_positions'][-1]  # Last frame
        else:
            target_pos = episode_data['joint_positions'][0]  # First frame
        
        # Get current position
        state = self.interface.get_joint_state()
        if state is None:
            self.console.print("[red]Failed to get robot state![/red]")
            return
        
        current_pos = state.positions
        
        # Get joint indices from metadata
        metadata = episode_data['metadata']
        joint_group = metadata.get('joint_group', 'all')
        joint_indices = metadata.get('joint_indices', None)
        if joint_indices is None:
            from ..core import get_joint_indices
            joint_indices = get_joint_indices(joint_group)
        
        # Smooth transition
        start_time = time.time()
        
        while time.time() - start_time < transition_duration:
            elapsed = time.time() - start_time
            ratio = elapsed / transition_duration
            
            # Smooth interpolation using cosine
            smooth_ratio = (1 - np.cos(ratio * np.pi)) / 2
            
            # Interpolate positions
            interpolated_pos = current_pos + (target_pos - current_pos) * smooth_ratio
            
            # Send command (only for specified joints)
            self.interface.send_joint_commands(interpolated_pos, joint_indices=joint_indices)
            
            time.sleep(0.002)  # 500Hz control
        
        # Send final target position
        self.interface.send_joint_commands(target_pos, joint_indices=joint_indices)
    
    def _play_episode(self, episode_path: str, playback_speed: float, skip_transition: bool = False):
        """
        Use existing Replayer to play an episode.
        
        Args:
            episode_path: Path to episode file
            playback_speed: Playback speed multiplier
            skip_transition: If True, start playing from current position without transitioning to start
        """
        replayer = Replayer(
            self.interface,
            self.data_manager,
            episode_path,
            playback_speed
        )
        
        # Play without confirmation (already confirmed at song level)
        replayer.running = True
        replayer.start_time = time.time()
        
        # Get current position for smooth transition (unless skipped)
        if not skip_transition:
            state = self.interface.get_joint_state()
            if state is not None:
                current_pos = state.positions
                target_pos = replayer.joint_positions[0]
                
                # Quick smooth transition (shorter than default)
                replayer.transition_duration = 1.0
                replayer._smooth_transition(current_pos, target_pos)
        
        # Play through the episode
        while replayer.running:
            current_time = time.time()
            elapsed = current_time - replayer.start_time
            playback_time = elapsed * playback_speed
            
            target_pos = replayer._get_target_position(playback_time)
            
            if target_pos is None:
                # Playback finished
                break
            
            # Send command
            self.interface.send_joint_commands(target_pos, joint_indices=replayer.joint_indices)
            
            time.sleep(0.002)  # 500Hz control
        
        # Hold final position briefly
        if target_pos is not None:
            for _ in range(25):  # ~50ms hold
                self.interface.send_joint_commands(target_pos, joint_indices=replayer.joint_indices)
                time.sleep(0.002)
    
    def _format_action_info(self, chord_action: ChordAction) -> str:
        """Format chord action info for display"""
        if len(chord_action.notes) == 1:
            note = chord_action.notes[0]
            if note.is_rest:
                return f"rest ({note.duration})"
            return f"{note.note} ({note.hand}, {note.duration})"
        else:
            note_strs = []
            for note in chord_action.notes:
                if not note.is_rest:
                    note_strs.append(f"{note.note}:{note.hand}")
            duration = chord_action.notes[0].duration
            return f"chord [{', '.join(note_strs)}] ({duration})"
    
    def _print_sequence_preview(self, actions: List[ChordAction], tempo_multiplier: float):
        """Print a preview of the sequence to be played"""
        from rich.table import Table
        
        table = Table(title="Sequence Preview", show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Action", style="cyan")
        table.add_column("Duration", justify="right", style="yellow")
        table.add_column("Wait (s)", justify="right", style="green")
        
        for i, action in enumerate(actions, 1):
            action_str = self._format_action_info(action)
            duration_type = action.notes[0].duration
            wait_time = action.duration_seconds * tempo_multiplier
            
            table.add_row(
                str(i),
                action_str,
                duration_type,
                f"{wait_time:.2f}"
            )
        
        total_duration = sum(a.duration_seconds for a in actions) * tempo_multiplier
        table.caption = f"Total duration: {total_duration:.2f}s"
        
        self.console.print(table)

