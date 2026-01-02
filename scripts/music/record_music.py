#!/usr/bin/env python3
"""CLI script for recording music episodes"""

import sys
import argparse
from pathlib import Path
from rich.console import Console

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from g1_record_replay.music import MusicConfig, MusicRecorder
from g1_record_replay.core import G1Interface, DataManager
from g1_record_replay.safety import SafetyChecker


def main():
    parser = argparse.ArgumentParser(
        description="Record music episodes for an instrument"
    )
    parser.add_argument(
        '--instrument',
        type=str,
        required=True,
        help='Instrument name'
    )
    parser.add_argument(
        '--notes',
        type=str,
        help='Comma-separated list of specific notes to record (e.g., C1,D1,E1)'
    )
    parser.add_argument(
        '--frequency',
        type=float,
        default=50.0,
        help='Recording frequency in Hz (default: 50)'
    )
    parser.add_argument(
        '--skip-init',
        action='store_true',
        help='Skip recording initial position'
    )
    parser.add_argument(
        '--skip-final',
        action='store_true',
        help='Skip recording final position'
    )
    parser.add_argument(
        '--interface',
        type=str,
        help='Network interface (e.g., eth0, enp2s0)'
    )
    parser.add_argument(
        '--skip-safety',
        action='store_true',
        help='Skip safety checks (NOT RECOMMENDED)'
    )
    parser.add_argument(
        '--list-status',
        action='store_true',
        help='List recording status and exit'
    )
    parser.add_argument(
        '--note-details',
        type=str,
        help='Show details for a specific note and exit'
    )
    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='Disable audio prompts (text-to-speech)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate recording without robot connection (for testing workflow)'
    )
    
    args = parser.parse_args()
    console = Console()
    
    # Load configuration
    try:
        config = MusicConfig.load(args.instrument)
    except FileNotFoundError:
        console.print(f"[red]Instrument configuration not found: {args.instrument}[/red]")
        console.print(f"[yellow]Create one with: python scripts/music/setup_music_config.py[/yellow]")
        return 1
    
    # Handle info commands that don't need robot connection
    if args.list_status or args.note_details:
        # Create a dummy interface for these operations
        data_manager = DataManager()
        recorder = MusicRecorder(config, None, data_manager, args.frequency, dry_run=True)
        
        if args.list_status:
            recorder.list_recorded_notes()
        
        if args.note_details:
            recorder.get_note_details(args.note_details)
        
        return 0
    
    # Dry run mode - no robot connection needed
    if args.dry_run:
        console.print("[bold yellow]🔍 Dry Run Mode[/bold yellow]")
        console.print("[yellow]Simulating recording workflow without robot connection[/yellow]\n")
        
        data_manager = DataManager()
        recorder = MusicRecorder(config, None, data_manager, args.frequency,
                                use_audio=not args.no_audio, dry_run=True)
        
        try:
            recorder.record_all_notes(
                skip_init=args.skip_init,
                skip_final=args.skip_final,
                specific_notes=specific_notes
            )
            
            console.print("\n[bold green]✓ Dry run complete![/bold green]")
            console.print("[cyan]Note: Configuration was updated but no actual episodes were recorded[/cyan]")
            console.print("[cyan]Run without --dry-run to record with the robot[/cyan]")
            return 0
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            return 1
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback
            traceback.print_exc()
            return 1
    
    # Parse specific notes if provided
    specific_notes = None
    if args.notes:
        specific_notes = [n.strip() for n in args.notes.split(',')]
        # Validate notes exist
        for note in specific_notes:
            if note not in config.notes:
                console.print(f"[red]Note '{note}' not found in configuration[/red]")
                return 1
    
    # Safety check
    if not args.skip_safety:
        safety_checker = SafetyChecker()
        if not safety_checker.pre_record_safety_check('arms'):
            console.print("[yellow]Recording cancelled for safety reasons.[/yellow]")
            return 1
    
    try:
        # Initialize interface
        console.print("[cyan]Initializing robot connection...[/cyan]")
        interface = G1Interface(args.interface, use_motion_switcher=True)
        interface.initialize()
        
        # Initialize data manager
        data_manager = DataManager()
        
        # Create recorder (dry_run=False for actual recording)
        recorder = MusicRecorder(config, interface, data_manager, args.frequency,
                                use_audio=not args.no_audio, dry_run=False)
        
        # Run recording
        recorder.record_all_notes(
            skip_init=args.skip_init,
            skip_final=args.skip_final,
            specific_notes=specific_notes
        )
        
        console.print("\n[bold green]✓ Recording session complete![/bold green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'interface' in locals() and interface is not None:
            interface.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

