"""Music Configuration Management"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from rich.console import Console


class MusicConfig:
    """Manages instrument configurations for music playback"""
    
    def __init__(self, instrument_name: str, config_dir: str = "data/music/configs"):
        """
        Initialize music configuration.
        
        Args:
            instrument_name: Name of the instrument
            config_dir: Directory for configuration files
        """
        self.instrument_name = instrument_name
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = self.config_dir / f"{instrument_name}.json"
        self.console = Console()
        
        # Configuration data
        self.description = ""
        self.tempo_bpm = 120  # Default tempo
        self.time_signature = "4/4"
        self.note_durations: Dict[str, float] = {}
        self.init_position_episode: Optional[str] = None
        self.final_position_episode: Optional[str] = None
        self.notes: Dict[str, Dict[str, Any]] = {}
        self.created_at: Optional[str] = None
        
        # Calculate default durations
        self._calculate_durations()
    
    def _calculate_durations(self):
        """Calculate note durations based on tempo"""
        beat_duration = 60.0 / self.tempo_bpm  # seconds per beat
        
        self.note_durations = {
            "full": beat_duration * 4,      # Whole note (4 beats)
            "half": beat_duration * 2,      # Half note (2 beats)
            "quarter": beat_duration * 1,   # Quarter note (1 beat)
            "eighth": beat_duration * 0.5,  # Eighth note (0.5 beats)
            "sixteenth": beat_duration * 0.25,  # Sixteenth note (0.25 beats)
            # Optional dotted notes (1.5x duration)
            "quarter_dotted": beat_duration * 1.5,
            "half_dotted": beat_duration * 3,
        }
    
    def set_tempo(self, bpm: int):
        """
        Set tempo in beats per minute and recalculate durations.
        
        Args:
            bpm: Beats per minute (typically 40-200)
        """
        if bpm < 40 or bpm > 240:
            raise ValueError(f"BPM must be between 40 and 240, got {bpm}")
        
        self.tempo_bpm = bpm
        self._calculate_durations()
        self.console.print(f"[green]Tempo set to {bpm} BPM[/green]")
    
    def set_time_signature(self, numerator: int, denominator: int):
        """
        Set time signature.
        
        Args:
            numerator: Number of beats per measure
            denominator: Note value that gets one beat
        """
        self.time_signature = f"{numerator}/{denominator}"
        self.console.print(f"[green]Time signature set to {self.time_signature}[/green]")
    
    def add_note(self, note_name: str, hand: str) -> Dict[str, Any]:
        """
        Add a note to the configuration.
        
        Args:
            note_name: Name of the note (e.g., 'C1', 'D2')
            hand: Which hand plays it ('left' or 'right')
            
        Returns:
            Note configuration dictionary
        """
        if hand not in ['left', 'right']:
            raise ValueError(f"Hand must be 'left' or 'right', got '{hand}'")
        
        if note_name in self.notes:
            self.console.print(f"[yellow]Warning: Note {note_name} already exists, updating...[/yellow]")
        
        # Create episode directory for this instrument
        episode_dir = Path(f"data/music/episodes/{self.instrument_name}")
        episode_dir.mkdir(parents=True, exist_ok=True)
        
        note_config = {
            "hand": hand,
            "episode_path": str(episode_dir / f"{note_name}_{hand}.h5"),
            "backup_path": None,
            "duration": None,
            "fps": None,
            "recorded_at": None
        }
        
        self.notes[note_name] = note_config
        return note_config
    
    def update_note_episode(self, note_name: str, episode_path: str, 
                           duration: float, fps: float):
        """
        Update episode information for a note after recording.
        
        Args:
            note_name: Name of the note
            episode_path: Path to the recorded episode
            duration: Duration of the episode in seconds
            fps: Recording frequency (frames per second)
        """
        if note_name not in self.notes:
            raise ValueError(f"Note {note_name} not found in configuration")
        
        self.notes[note_name].update({
            "episode_path": episode_path,
            "duration": duration,
            "fps": fps,
            "recorded_at": datetime.now().isoformat()
        })
    
    def get_note_info(self, note_name: str) -> Dict[str, Any]:
        """
        Get information about a specific note.
        
        Args:
            note_name: Name of the note
            
        Returns:
            Note configuration dictionary
        """
        if note_name not in self.notes:
            raise ValueError(f"Note {note_name} not found in configuration")
        
        return self.notes[note_name]
    
    def list_notes(self, hand: Optional[str] = None) -> List[str]:
        """
        List all configured notes.
        
        Args:
            hand: Filter by hand ('left', 'right', or None for all)
            
        Returns:
            List of note names
        """
        if hand is None:
            return list(self.notes.keys())
        
        if hand not in ['left', 'right']:
            raise ValueError(f"Hand must be 'left', 'right', or None, got '{hand}'")
        
        return [name for name, config in self.notes.items() 
                if config['hand'] == hand]
    
    def set_init_position(self, episode_path: str):
        """Set the initial position episode path"""
        self.init_position_episode = episode_path
    
    def set_final_position(self, episode_path: str):
        """Set the final position episode path"""
        self.final_position_episode = episode_path
    
    def validate_config(self) -> bool:
        """
        Validate configuration integrity.
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        errors = []
        
        # Check if we have at least one note
        if not self.notes:
            errors.append("No notes configured")
        
        # Check if init/final positions are set
        if not self.init_position_episode:
            errors.append("Initial position episode not set")
        
        if not self.final_position_episode:
            errors.append("Final position episode not set")
        
        # Check for duplicate note-hand combinations
        note_hand_pairs = [(name, config['hand']) 
                          for name, config in self.notes.items()]
        if len(note_hand_pairs) != len(set(note_hand_pairs)):
            errors.append("Duplicate note-hand combinations found")
        
        if errors:
            raise ValueError("Configuration validation failed:\n  " + "\n  ".join(errors))
        
        return True
    
    def save(self, filepath: Optional[str] = None):
        """
        Save configuration to JSON file.
        
        Args:
            filepath: Optional custom filepath (defaults to standard location)
        """
        if filepath:
            save_path = Path(filepath)
        else:
            save_path = self.config_path
        
        # Update created_at if not set
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        
        config_data = {
            "instrument_name": self.instrument_name,
            "description": self.description,
            "tempo_bpm": self.tempo_bpm,
            "time_signature": self.time_signature,
            "note_durations": self.note_durations,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(),
            "init_position_episode": self.init_position_episode,
            "final_position_episode": self.final_position_episode,
            "notes": self.notes
        }
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        self.console.print(f"[bold green]✓ Configuration saved: {save_path}[/bold green]")
    
    @classmethod
    def load(cls, instrument_name: str, config_dir: str = "data/music/configs") -> 'MusicConfig':
        """
        Load configuration from JSON file.
        
        Args:
            instrument_name: Name of the instrument
            config_dir: Directory containing configuration files
            
        Returns:
            MusicConfig instance
        """
        config = cls(instrument_name, config_dir)
        config_path = config.config_path
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration not found: {config_path}")
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # Load all fields
        config.description = data.get("description", "")
        config.tempo_bpm = data.get("tempo_bpm", 120)
        config.time_signature = data.get("time_signature", "4/4")
        config.note_durations = data.get("note_durations", {})
        config.created_at = data.get("created_at")
        config.init_position_episode = data.get("init_position_episode")
        config.final_position_episode = data.get("final_position_episode")
        config.notes = data.get("notes", {})
        
        # Recalculate durations if needed
        if not config.note_durations:
            config._calculate_durations()
        
        console = Console()
        console.print(f"[green]Configuration loaded: {config_path}[/green]")
        
        return config
    
    @staticmethod
    def list_instruments(config_dir: str = "data/music/configs") -> List[str]:
        """
        List all available instrument configurations.
        
        Args:
            config_dir: Directory containing configuration files
            
        Returns:
            List of instrument names
        """
        config_path = Path(config_dir)
        if not config_path.exists():
            return []
        
        return [f.stem for f in config_path.glob("*.json")]
    
    def print_summary(self):
        """Print a summary of the configuration"""
        from rich.table import Table
        from rich.panel import Panel
        
        self.console.print(f"\n[bold cyan]Configuration: {self.instrument_name}[/bold cyan]")
        
        if self.description:
            self.console.print(f"Description: {self.description}")
        
        self.console.print(f"Tempo: {self.tempo_bpm} BPM")
        self.console.print(f"Time Signature: {self.time_signature}")
        
        # Note durations
        self.console.print("\n[bold]Note Durations:[/bold]")
        for duration, seconds in self.note_durations.items():
            self.console.print(f"  {duration}: {seconds:.3f}s")
        
        # Position episodes
        self.console.print(f"\n[bold]Position Episodes:[/bold]")
        self.console.print(f"  Init: {self.init_position_episode or '[red]Not set[/red]'}")
        self.console.print(f"  Final: {self.final_position_episode or '[red]Not set[/red]'}")
        
        # Notes table
        if self.notes:
            table = Table(title=f"\nConfigured Notes ({len(self.notes)} total)", 
                         show_header=True, header_style="bold cyan")
            table.add_column("Note", style="cyan")
            table.add_column("Hand", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("Duration (s)", justify="right")
            table.add_column("FPS", justify="right")
            
            for note_name in sorted(self.notes.keys()):
                note = self.notes[note_name]
                status = "✓ Recorded" if note['recorded_at'] else "○ Not recorded"
                duration = f"{note['duration']:.2f}" if note['duration'] else "-"
                fps = f"{note['fps']:.1f}" if note['fps'] else "-"
                
                table.add_row(note_name, note['hand'], status, duration, fps)
            
            self.console.print(table)
        else:
            self.console.print("\n[yellow]No notes configured yet[/yellow]")

