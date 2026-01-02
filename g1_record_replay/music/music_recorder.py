"""Music Recorder - Record episodes for musical notes"""

import time
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from ..core import G1Interface, DataManager
from ..record import Recorder
from .music_config import MusicConfig


class MusicRecorder:
    """Orchestrates recording of all music notes for an instrument"""
    
    def __init__(self, config: MusicConfig, interface: Optional[G1Interface], 
                 data_manager: DataManager, frequency: float = 50.0,
                 use_audio: bool = True, dry_run: bool = False):
        """
        Initialize music recorder.
        
        Args:
            config: MusicConfig instance
            interface: G1Interface instance (None for dry-run mode)
            data_manager: DataManager instance
            frequency: Recording frequency in Hz
            use_audio: Whether to use audio prompts (text-to-speech)
            dry_run: If True, simulate recording without robot connection
        """
        self.config = config
        self.interface = interface
        self.data_manager = data_manager
        self.frequency = frequency
        self.use_audio = use_audio
        self.dry_run = dry_run
        self.console = Console()
        
        # Track recording status
        self.recorded_notes: List[str] = []
        self.skipped_notes: List[str] = []
        
        # Check if text-to-speech is available
        if self.use_audio:
            self.tts_available = self._check_tts_available()
            if not self.tts_available:
                self.console.print("[yellow]Text-to-speech not available, audio prompts disabled[/yellow]")
                self.use_audio = False
    
    def _check_tts_available(self) -> bool:
        """
        Check if text-to-speech is available on the system.
        
        Returns:
            True if TTS is available, False otherwise
        """
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                # Check if 'say' command exists
                subprocess.run(['which', 'say'], capture_output=True, check=True)
                return True
            elif system == "Linux":
                # Check if 'espeak' or 'spd-say' exists
                try:
                    subprocess.run(['which', 'espeak'], capture_output=True, check=True)
                    return True
                except:
                    try:
                        subprocess.run(['which', 'spd-say'], capture_output=True, check=True)
                        return True
                    except:
                        return False
            else:
                return False
        except:
            return False
    
    def _speak(self, text: str, wait: bool = True):
        """
        Speak text using text-to-speech.
        
        Args:
            text: Text to speak
            wait: Whether to wait for speech to complete
        """
        if not self.use_audio or not self.tts_available:
            return
        
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                cmd = ['say', text]
            elif system == "Linux":
                # Try espeak first, then spd-say
                try:
                    subprocess.run(['which', 'espeak'], capture_output=True, check=True)
                    cmd = ['espeak', text]
                except:
                    cmd = ['spd-say', text]
            else:
                return
            
            if wait:
                subprocess.run(cmd, capture_output=True)
            else:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            # Silently fail if TTS fails
            pass
    
    def record_all_notes(self, skip_init: bool = False, skip_final: bool = False,
                        specific_notes: Optional[List[str]] = None):
        """
        Record all notes in the configuration.
        
        Args:
            skip_init: Skip recording initial position
            skip_final: Skip recording final position
            specific_notes: Only record these notes (None = all)
        """
        mode_text = "[yellow]DRY RUN MODE[/yellow]" if self.dry_run else ""
        self.console.print(Panel.fit(
            f"[bold cyan]🎵 Recording Music Episodes[/bold cyan] {mode_text}\n"
            f"Instrument: {self.config.instrument_name}\n"
            f"Frequency: {self.frequency} Hz",
            border_style="cyan"
        ))
        
        if self.dry_run:
            self.console.print("[yellow]ℹ️  Dry run mode: Simulating recording without robot connection[/yellow]")
            self.console.print("[yellow]   All steps will be shown but no actual recordings will be made[/yellow]\n")
        
        # Record init position
        if not skip_init:
            if not self._record_init_position():
                self.console.print("[yellow]Aborted by user[/yellow]")
                return
        
        # Get notes to record
        if specific_notes:
            notes_to_record = specific_notes
        else:
            notes_to_record = list(self.config.notes.keys())
        
        if not notes_to_record:
            self.console.print("[yellow]No notes to record[/yellow]")
            return
        
        # Group by hand for organized recording
        left_notes = [n for n in notes_to_record 
                     if self.config.notes[n]['hand'] == 'left']
        right_notes = [n for n in notes_to_record 
                      if self.config.notes[n]['hand'] == 'right']
        
        # Record right hand notes first
        if right_notes:
            self.console.print(f"\n[bold cyan]Recording Right Hand Notes ({len(right_notes)})[/bold cyan]")
            for note in right_notes:
                if not self._record_note(note):
                    if not Confirm.ask("Continue with remaining notes?", default=True):
                        break
        
        # Record left hand notes
        if left_notes:
            self.console.print(f"\n[bold cyan]Recording Left Hand Notes ({len(left_notes)})[/bold cyan]")
            for note in left_notes:
                if not self._record_note(note):
                    if not Confirm.ask("Continue with remaining notes?", default=True):
                        break
        
        # Record final position
        if not skip_final:
            self._record_final_position()
        
        # Print summary
        self._print_summary()
        
        # Save updated config
        self.config.save()
    
    def _record_init_position(self) -> bool:
        """
        Record initial position episode.
        
        Returns:
            True if recorded successfully, False if skipped/cancelled
        """
        self.console.print("\n[bold yellow]Initial Position Recording[/bold yellow]")
        self._speak("Recording initial position")
        
        self.console.print("This is the starting position from which G1 will begin playing music.")
        self.console.print("Typically: G1 sitting on a chair with arms in a neutral/rest position.\n")
        
        # Check if already exists
        if self.config.init_position_episode and Path(self.config.init_position_episode).exists():
            self.console.print(f"[yellow]Init position already recorded: {self.config.init_position_episode}[/yellow]")
            if not Confirm.ask("Re-record?", default=False):
                return True
        
        if not Confirm.ask("[bold]Ready to record initial position?[/bold]", default=True):
            return False
        
        self.console.print("\n[cyan]Instructions:[/cyan]")
        self.console.print("  1. Position G1 in sitting position on a chair")
        self.console.print("  2. Place arms in neutral/rest position")
        self.console.print("  3. Recording will start when you press Enter")
        self.console.print("  4. Slowly move arms from rest to ready position (above instrument)")
        self.console.print("  5. Press 'S' to stop recording\n")
        
        self._speak("Ready to record. Press enter to start.")
        
        if self.dry_run:
            self.console.print("[dim]Dry run: Skipping actual recording[/dim]")
            self.console.print("[cyan]Simulating 3-second init position recording...[/cyan]")
            time.sleep(1)  # Brief pause to simulate
            duration = 3.0
            num_frames = int(duration * self.frequency)
            self.console.print(f"[green]✓ Init position simulated: {duration:.2f}s, {num_frames} frames[/green]")
            return True
        
        Prompt.ask("Press Enter when ready to start")
        
        try:
            # Record using existing Recorder class
            recorder = Recorder(
                self.interface,
                self.data_manager,
                self.frequency,
                episode_name=f"{self.config.instrument_name}_init-position",
                joint_group="arms",
                show_positions=False
            )
            
            recorder.run()
            
            # Update config with recorded episode
            if len(recorder.timestamps) > 0:
                episode_path = self.config.init_position_episode
                # The recorder already saved the file, we just need to update config
                duration = recorder.timestamps[-1] if len(recorder.timestamps) > 0 else 0
                self.config.init_position_episode = episode_path
                self.console.print(f"[green]✓ Init position recorded: {duration:.2f}s[/green]")
                return True
            else:
                self.console.print("[yellow]Recording cancelled[/yellow]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error recording: {e}[/red]")
            return False
    
    def _record_final_position(self) -> bool:
        """
        Record final position episode.
        
        Returns:
            True if recorded successfully, False if skipped/cancelled
        """
        self.console.print("\n[bold yellow]Final Position Recording[/bold yellow]")
        self._speak("Recording final position")
        
        self.console.print("This is the ending position to which G1 will return after playing.\n")
        
        # Check if already exists
        if self.config.final_position_episode and Path(self.config.final_position_episode).exists():
            self.console.print(f"[yellow]Final position already recorded: {self.config.final_position_episode}[/yellow]")
            if not Confirm.ask("Re-record?", default=False):
                return True
        
        if not Confirm.ask("[bold]Ready to record final position?[/bold]", default=True):
            return False
        
        self.console.print("\n[cyan]Instructions:[/cyan]")
        self.console.print("  1. Start with arms in ready position (above instrument)")
        self.console.print("  2. Recording will start when you press Enter")
        self.console.print("  3. Slowly move arms back to rest position")
        self.console.print("  4. Press 'S' to stop recording\n")
        
        self._speak("Ready to record. Press enter to start.")
        
        if self.dry_run:
            self.console.print("[dim]Dry run: Skipping actual recording[/dim]")
            self.console.print("[cyan]Simulating 3-second final position recording...[/cyan]")
            time.sleep(1)  # Brief pause to simulate
            duration = 3.0
            num_frames = int(duration * self.frequency)
            self.console.print(f"[green]✓ Final position simulated: {duration:.2f}s, {num_frames} frames[/green]")
            return True
        
        Prompt.ask("Press Enter when ready to start")
        
        try:
            recorder = Recorder(
                self.interface,
                self.data_manager,
                self.frequency,
                episode_name=f"{self.config.instrument_name}_final-position",
                joint_group="arms",
                show_positions=False
            )
            
            recorder.run()
            
            if len(recorder.timestamps) > 0:
                episode_path = self.config.final_position_episode
                duration = recorder.timestamps[-1] if len(recorder.timestamps) > 0 else 0
                self.config.final_position_episode = episode_path
                self.console.print(f"[green]✓ Final position recorded: {duration:.2f}s[/green]")
                return True
            else:
                self.console.print("[yellow]Recording cancelled[/yellow]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error recording: {e}[/red]")
            return False
    
    def _record_note(self, note_name: str) -> bool:
        """
        Record a single note episode.
        
        Args:
            note_name: Name of the note to record
            
        Returns:
            True if recorded successfully, False if skipped/cancelled
        """
        note_config = self.config.notes[note_name]
        hand = note_config['hand']
        episode_path = note_config['episode_path']
        
        self.console.print(f"\n[bold cyan]Recording: {note_name} ({hand} hand)[/bold cyan]")
        
        # Audio prompt - announce the note
        self._speak(f"Recording note {note_name}, {hand} hand")
        
        # Check if already recorded
        if Path(episode_path).exists():
            self.console.print(f"[yellow]Already recorded: {episode_path}[/yellow]")
            if not Confirm.ask("Re-record?", default=False):
                self.skipped_notes.append(note_name)
                return True
        
        self.console.print("\n[cyan]Instructions:[/cyan]")
        self.console.print(f"  1. Position {hand} hand above the {note_name} key/pad")
        self.console.print(f"  2. Recording will start when you press Enter")
        self.console.print(f"  3. Press/hit the key to play the note")
        self.console.print(f"  4. Return hand to starting position")
        self.console.print(f"  5. Press 'S' to stop recording")
        
        choice = Prompt.ask(
            "\n[bold]Options[/bold]",
            choices=["r", "s", "q"],
            default="r",
            show_choices=False
        )
        
        self.console.print("  [r] Record  [s] Skip  [q] Quit")
        
        if choice == 'q':
            return False
        elif choice == 's':
            self.skipped_notes.append(note_name)
            return True
        
        # Audio prompt before recording starts
        self._speak(f"Ready to record {note_name}. Press enter to start.")
        
        if self.dry_run:
            self.console.print("[dim]Dry run: Skipping actual recording[/dim]")
            # Simulate different note durations (0.5-1.0 seconds)
            import random
            duration = random.uniform(0.5, 1.0)
            num_frames = int(duration * self.frequency)
            self.console.print(f"[cyan]Simulating {duration:.2f}s note recording...[/cyan]")
            time.sleep(0.5)  # Brief pause to simulate
            
            # Update config with simulated episode info
            self.config.update_note_episode(
                note_name,
                episode_path,
                duration,
                self.frequency
            )
            self.recorded_notes.append(note_name)
            self.console.print(f"[green]✓ {note_name} simulated: {duration:.2f}s, {num_frames} frames[/green]")
            return True
        
        try:
            # Record using existing Recorder class
            recorder = Recorder(
                self.interface,
                self.data_manager,
                self.frequency,
                episode_name=f"{self.config.instrument_name}_{note_name}_{hand}",
                joint_group="arms",
                show_positions=False
            )
            
            recorder.run()
            
            # Update config with recorded episode info
            if len(recorder.timestamps) > 0:
                duration = recorder.timestamps[-1] if len(recorder.timestamps) > 0 else 0
                self.config.update_note_episode(
                    note_name,
                    episode_path,
                    duration,
                    self.frequency
                )
                self.recorded_notes.append(note_name)
                self.console.print(f"[green]✓ {note_name} recorded: {duration:.2f}s, {len(recorder.timestamps)} frames[/green]")
                return True
            else:
                self.console.print("[yellow]Recording cancelled[/yellow]")
                self.skipped_notes.append(note_name)
                return True
                
        except Exception as e:
            self.console.print(f"[red]Error recording: {e}[/red]")
            self.skipped_notes.append(note_name)
            return True
    
    def _print_summary(self):
        """Print recording summary"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold cyan]Recording Summary[/bold cyan]")
        self.console.print("="*60)
        
        self.console.print(f"\n[green]✓ Recorded: {len(self.recorded_notes)} notes[/green]")
        for note in self.recorded_notes:
            self.console.print(f"    {note}")
        
        if self.skipped_notes:
            self.console.print(f"\n[yellow]○ Skipped: {len(self.skipped_notes)} notes[/yellow]")
            for note in self.skipped_notes:
                self.console.print(f"    {note}")
        
        total_notes = len(self.config.notes)
        recorded_count = sum(1 for n in self.config.notes.values() 
                           if n['recorded_at'] is not None)
        
        self.console.print(f"\n[bold]Total Progress: {recorded_count}/{total_notes} notes recorded[/bold]")
    
    def list_recorded_notes(self):
        """Display recording status for all notes"""
        table = Table(title=f"Recording Status: {self.config.instrument_name}", 
                     show_header=True, header_style="bold cyan")
        table.add_column("Note", style="cyan")
        table.add_column("Hand", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Duration", justify="right")
        table.add_column("Frames", justify="right")
        table.add_column("File", style="dim")
        
        for note_name in sorted(self.config.notes.keys()):
            note = self.config.notes[note_name]
            
            if note['recorded_at']:
                status = "✓ Recorded"
                duration = f"{note['duration']:.2f}s" if note['duration'] else "-"
                fps = note['fps'] or 0
                frames = int(note['duration'] * fps) if note['duration'] and fps else 0
                file_exists = "✓" if Path(note['episode_path']).exists() else "✗"
            else:
                status = "○ Not recorded"
                duration = "-"
                frames = 0
                file_exists = "-"
            
            table.add_row(
                note_name,
                note['hand'],
                status,
                duration,
                str(frames) if frames > 0 else "-",
                file_exists
            )
        
        self.console.print(table)
    
    def get_note_details(self, note_name: str):
        """
        Print comprehensive details about a specific note.
        
        Args:
            note_name: Name of the note
        """
        if note_name not in self.config.notes:
            self.console.print(f"[red]Note '{note_name}' not found in configuration[/red]")
            return
        
        note = self.config.notes[note_name]
        
        self.console.print(f"\n[bold cyan]Note Details: {note_name}[/bold cyan]")
        self.console.print(f"  Hand: {note['hand']}")
        self.console.print(f"  Episode Path: {note['episode_path']}")
        
        if note['recorded_at']:
            self.console.print(f"  [green]Status: Recorded[/green]")
            self.console.print(f"  Recorded At: {note['recorded_at']}")
            self.console.print(f"  Duration: {note['duration']:.2f}s")
            self.console.print(f"  FPS: {note['fps']:.1f}")
            self.console.print(f"  Frames: {int(note['duration'] * note['fps'])}")
            
            # Check if file exists
            if Path(note['episode_path']).exists():
                file_size = Path(note['episode_path']).stat().st_size / 1024  # KB
                self.console.print(f"  File Size: {file_size:.1f} KB")
                self.console.print(f"  [green]File exists: ✓[/green]")
            else:
                self.console.print(f"  [red]File exists: ✗ (Missing!)[/red]")
            
            # Backup info
            if note['backup_path']:
                self.console.print(f"  Backup: {note['backup_path']}")
        else:
            self.console.print(f"  [yellow]Status: Not recorded[/yellow]")

