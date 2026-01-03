#!/usr/bin/env python3
"""CLI script for playing music sequences"""

import sys
import argparse
from pathlib import Path
from rich.console import Console

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from g1_record_replay.music import MusicConfig, MusicReplayer
from g1_record_replay.core import G1Interface, DataManager
from g1_record_replay.safety import SafetyChecker


def load_song_file(filepath: str) -> str:
    """
    Load song sequence from a text file.
    
    Format:
        # Comment lines start with #
        # Blank lines are ignored
        
        # Each line is a phrase/measure
        C1:left:quarter -> D1:left:quarter -> E1:left:half
        rest:none:quarter -> F1:right:quarter
        
    Args:
        filepath: Path to song file
        
    Returns:
        Combined sequence string
    """
    sequence_parts = []
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip comments and blank lines
            if not line or line.startswith('#'):
                continue
            
            sequence_parts.append(line)
    
    return ' -> '.join(sequence_parts)


def main():
    parser = argparse.ArgumentParser(
        description="Play music on the G1 robot"
    )
    parser.add_argument(
        '--instrument',
        type=str,
        required=True,
        help='Instrument name'
    )
    
    # Sequence input (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--sequence',
        type=str,
        help='Note sequence string (e.g., "C1:left:quarter -> D1:left:half")'
    )
    group.add_argument(
        '--song-file',
        type=str,
        help='Load sequence from a song file'
    )
    
    # Playback options
    parser.add_argument(
        '--speed',
        type=float,
        default=1.0,
        help='Playback speed multiplier for init/final positions (default: 1.0)'
    )
    parser.add_argument(
        '--note-speed',
        type=float,
        default=None,
        help='Playback speed multiplier for notes only (default: same as --speed)'
    )
    parser.add_argument(
        '--tempo-multiplier',
        type=float,
        default=1.0,
        help='Tempo multiplier for timing between notes (default: 1.0)'
    )
    parser.add_argument(
        '--override-bpm',
        type=int,
        help='Override tempo BPM temporarily'
    )
    parser.add_argument(
        '--skip-init',
        action='store_true',
        help='Skip initial position transition'
    )
    parser.add_argument(
        '--skip-final',
        action='store_true',
        help='Skip final position transition'
    )
    
    # Robot options
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
    
    # Validation
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate sequence without playing'
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show instrument configuration and exit'
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
    
    # Show config and exit
    if args.show_config:
        config.print_summary()
        return 0
    
    # Override tempo if requested
    if args.override_bpm:
        original_bpm = config.tempo_bpm
        config.set_tempo(args.override_bpm)
        console.print(f"[yellow]Tempo overridden: {original_bpm} -> {args.override_bpm} BPM[/yellow]")
    
    # Get sequence
    if args.song_file:
        try:
            sequence = load_song_file(args.song_file)
            console.print(f"[cyan]Loaded song from: {args.song_file}[/cyan]")
        except FileNotFoundError:
            console.print(f"[red]Song file not found: {args.song_file}[/red]")
            return 1
        except Exception as e:
            console.print(f"[red]Error loading song file: {e}[/red]")
            return 1
    else:
        sequence = args.sequence
    
    # Validate speed parameters
    if args.speed <= 0 or args.speed > 2.0:
        console.print("[red]Speed must be between 0 and 2.0[/red]")
        return 1
    
    if args.note_speed is not None and (args.note_speed <= 0 or args.note_speed > 5.0):
        console.print("[red]Note speed must be between 0 and 5.0[/red]")
        return 1
    
    if args.tempo_multiplier <= 0 or args.tempo_multiplier > 3.0:
        console.print("[red]Tempo multiplier must be between 0 and 3.0[/red]")
        return 1
    
    # Dry run mode - validate without robot connection
    if args.dry_run:
        console.print("[yellow]Dry run mode - validating sequence only[/yellow]\n")
        
        try:
            # Create dummy replayer for validation
            data_manager = DataManager()
            replayer = MusicReplayer(config, None, data_manager)
            
            # Parse and validate
            actions = replayer.parse_sequence(sequence)
            console.print(f"[green]✓ Parsed {len(actions)} actions[/green]")
            
            replayer.validate_sequence(actions)
            console.print("[green]✓ Sequence is valid[/green]\n")
            
            # Show preview
            replayer._print_sequence_preview(actions, args.tempo_multiplier)
            
            return 0
            
        except Exception as e:
            console.print(f"[red]Validation failed: {e}[/red]")
            return 1
    
    # Safety check
    if not args.skip_safety:
        safety_checker = SafetyChecker()
        if not safety_checker.pre_replay_safety_check('arms'):
            console.print("[yellow]Playback cancelled for safety reasons.[/yellow]")
            return 1
    else:
        console.print("[bold red]⚠️ SAFETY CHECKS SKIPPED - DANGEROUS! ⚠️[/bold red]")
    
    try:
        # Initialize interface
        console.print("[cyan]Initializing robot connection...[/cyan]")
        interface = G1Interface(args.interface, use_motion_switcher=True)
        interface.initialize()
        
        # Initialize data manager
        data_manager = DataManager()
        
        # Create replayer
        replayer = MusicReplayer(config, interface, data_manager)
        
        # Play the song
        replayer.play_song(
            sequence,
            playback_speed=args.speed,
            tempo_multiplier=args.tempo_multiplier,
            skip_init=args.skip_init,
            skip_final=args.skip_final,
            note_speed=args.note_speed
        )
        
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

