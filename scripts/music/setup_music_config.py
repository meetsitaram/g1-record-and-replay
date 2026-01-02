#!/usr/bin/env python3
"""Interactive setup script for creating music instrument configurations"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

# Add parent directory to path to import g1_record_replay
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from g1_record_replay.music import MusicConfig


def main():
    parser = argparse.ArgumentParser(
        description="Setup music instrument configuration"
    )
    parser.add_argument(
        '--instrument',
        type=str,
        help='Instrument name (interactive if not provided)'
    )
    parser.add_argument(
        '--edit',
        action='store_true',
        help='Edit existing configuration'
    )
    parser.add_argument(
        '--batch-file',
        type=str,
        help='Import notes from CSV file (format: note,hand)'
    )
    
    args = parser.parse_args()
    console = Console()
    
    # Print header
    console.print(Panel.fit(
        "[bold cyan]🎵 Music Configuration Setup[/bold cyan]\n"
        "Create or edit instrument configurations for G1 music playback",
        border_style="cyan"
    ))
    
    # Get or create instrument
    if args.edit or args.instrument:
        if not args.instrument:
            # List available instruments
            instruments = MusicConfig.list_instruments()
            if not instruments:
                console.print("[red]No instruments configured yet. Create a new one.[/red]")
                args.edit = False
            else:
                console.print("\n[cyan]Available instruments:[/cyan]")
                for i, inst in enumerate(instruments, 1):
                    console.print(f"  {i}. {inst}")
                
                choice = Prompt.ask(
                    "\nSelect instrument number or enter new name",
                    default="1"
                )
                
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(instruments):
                        args.instrument = instruments[idx]
                    else:
                        args.instrument = choice
                        args.edit = False
                except ValueError:
                    args.instrument = choice
                    args.edit = False
        
        if args.edit:
            try:
                config = MusicConfig.load(args.instrument)
                console.print(f"[green]Loaded existing configuration: {args.instrument}[/green]")
            except FileNotFoundError:
                console.print(f"[yellow]Configuration not found. Creating new one.[/yellow]")
                config = MusicConfig(args.instrument)
                args.edit = False
        else:
            config = MusicConfig(args.instrument)
    else:
        # Interactive instrument name
        instrument_name = Prompt.ask(
            "\n[bold cyan]Enter instrument name[/bold cyan]",
            default="piano"
        )
        config = MusicConfig(instrument_name)
    
    # Description
    if not args.edit or not config.description:
        description = Prompt.ask(
            "[bold cyan]Enter description[/bold cyan] (optional)",
            default=config.description or ""
        )
        if description:
            config.description = description
    
    # Tempo
    if not args.edit or Confirm.ask(f"Change tempo? (current: {config.tempo_bpm} BPM)", default=False):
        tempo = Prompt.ask(
            "[bold cyan]Enter tempo in BPM[/bold cyan]",
            default=str(config.tempo_bpm)
        )
        try:
            config.set_tempo(int(tempo))
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1
    
    # Time signature
    if not args.edit or Confirm.ask(f"Change time signature? (current: {config.time_signature})", default=False):
        time_sig = Prompt.ask(
            "[bold cyan]Enter time signature[/bold cyan] (e.g., 4/4, 3/4, 6/8)",
            default=config.time_signature
        )
        try:
            numerator, denominator = time_sig.split('/')
            config.set_time_signature(int(numerator), int(denominator))
        except:
            console.print(f"[red]Invalid time signature format[/red]")
            return 1
    
    # Notes configuration
    if args.batch_file:
        # Import from CSV
        console.print(f"\n[cyan]Importing notes from {args.batch_file}...[/cyan]")
        try:
            with open(args.batch_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) != 2:
                        console.print(f"[yellow]Line {line_num}: Invalid format, skipping[/yellow]")
                        continue
                    
                    note_name, hand = parts[0].strip(), parts[1].strip()
                    try:
                        config.add_note(note_name, hand)
                        console.print(f"[green]  ✓ Added {note_name} ({hand})[/green]")
                    except ValueError as e:
                        console.print(f"[red]  ✗ Line {line_num}: {e}[/red]")
        except FileNotFoundError:
            console.print(f"[red]File not found: {args.batch_file}[/red]")
            return 1
    else:
        # Interactive note configuration
        console.print("\n[bold cyan]Configure Notes[/bold cyan]")
        
        if config.notes:
            console.print(f"[yellow]Currently configured: {len(config.notes)} notes[/yellow]")
            if not Confirm.ask("Add more notes?", default=True):
                # Skip to save
                pass
            else:
                add_notes_interactive(config, console)
        else:
            if Confirm.ask("Add notes now?", default=True):
                add_notes_interactive(config, console)
    
    # Position episodes
    console.print("\n[bold cyan]Position Episodes[/bold cyan]")
    console.print("[dim]These will be recorded separately using the recording script[/dim]")
    
    if not config.init_position_episode:
        episode_dir = Path(f"data/music/episodes/{config.instrument_name}")
        episode_dir.mkdir(parents=True, exist_ok=True)
        config.set_init_position(str(episode_dir / "init-position.h5"))
    
    if not config.final_position_episode:
        episode_dir = Path(f"data/music/episodes/{config.instrument_name}")
        config.set_final_position(str(episode_dir / "final-position.h5"))
    
    console.print(f"  Init: {config.init_position_episode}")
    console.print(f"  Final: {config.final_position_episode}")
    
    # Summary
    console.print("\n")
    config.print_summary()
    
    # Save
    if Confirm.ask("\n[bold green]Save configuration?[/bold green]", default=True):
        try:
            config.save()
            console.print(f"\n[bold green]✓ Configuration saved successfully![/bold green]")
            console.print(f"\n[cyan]Next steps:[/cyan]")
            console.print(f"  1. Record episodes: python scripts/music/record_music.py --instrument {config.instrument_name}")
            console.print(f"  2. Play music: python scripts/music/play_music.py --instrument {config.instrument_name} --sequence '...'")
        except Exception as e:
            console.print(f"[red]Error saving configuration: {e}[/red]")
            return 1
    else:
        console.print("[yellow]Configuration not saved[/yellow]")
    
    return 0


def add_notes_interactive(config: MusicConfig, console: Console):
    """Interactively add notes to configuration"""
    num_notes = Prompt.ask(
        "How many notes to add?",
        default="8"
    )
    
    try:
        num_notes = int(num_notes)
    except ValueError:
        console.print("[red]Invalid number[/red]")
        return
    
    for i in range(num_notes):
        console.print(f"\n[bold]Note {i+1}/{num_notes}[/bold]")
        
        note_name = Prompt.ask("  Note name (e.g., C1, D2, E3)")
        
        hand = Prompt.ask(
            "  Hand",
            choices=["left", "right"],
            default="right"
        )
        
        try:
            config.add_note(note_name, hand)
            console.print(f"[green]  ✓ Added {note_name} ({hand})[/green]")
        except ValueError as e:
            console.print(f"[red]  ✗ Error: {e}[/red]")
            if not Confirm.ask("Continue?", default=True):
                break


if __name__ == "__main__":
    sys.exit(main())

