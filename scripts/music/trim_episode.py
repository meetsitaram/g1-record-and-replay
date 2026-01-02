#!/usr/bin/env python3
"""CLI script for trimming music episodes"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from g1_record_replay.music import MusicConfig, EpisodeTrimmer
from g1_record_replay.core import DataManager, G1Interface


def main():
    parser = argparse.ArgumentParser(
        description="Trim music episodes"
    )
    
    # Episode selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--episode',
        type=str,
        help='Direct path to episode file'
    )
    group.add_argument(
        '--note',
        type=str,
        help='Note name (requires --instrument)'
    )
    
    parser.add_argument(
        '--instrument',
        type=str,
        help='Instrument name (required with --note)'
    )
    
    # Trimming options
    parser.add_argument(
        '--trim-start',
        type=int,
        help='Number of frames to trim from start'
    )
    parser.add_argument(
        '--trim-end',
        type=int,
        help='Number of frames to trim from end'
    )
    parser.add_argument(
        '--start-time',
        type=float,
        help='Start time in seconds (trim everything before)'
    )
    parser.add_argument(
        '--end-time',
        type=float,
        help='End time in seconds (trim everything after)'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: overwrite original with backup)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup when overwriting'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview changes without saving (text-only, safe)'
    )
    parser.add_argument(
        '--visual-preview',
        action='store_true',
        help='Preview with robot movement (requires --interface, moves robot!)'
    )
    parser.add_argument(
        '--interface',
        type=str,
        help='Network interface for visual preview (e.g., eth0, enp2s0)'
    )
    
    args = parser.parse_args()
    console = Console()
    
    # Determine episode path
    if args.note:
        if not args.instrument:
            console.print("[red]Error: --instrument required when using --note[/red]")
            return 1
        
        try:
            config = MusicConfig.load(args.instrument)
            note_info = config.get_note_info(args.note)
            episode_path = note_info['episode_path']
            
            if not Path(episode_path).exists():
                console.print(f"[red]Episode not found for note {args.note}[/red]")
                console.print(f"[yellow]Record it first: python scripts/music/record_music.py --instrument {args.instrument} --notes {args.note}[/yellow]")
                return 1
        except FileNotFoundError:
            console.print(f"[red]Instrument configuration not found: {args.instrument}[/red]")
            return 1
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            return 1
    else:
        episode_path = args.episode
    
    # Check if any trimming operation specified
    if not any([args.trim_start, args.trim_end, args.start_time, args.end_time, args.preview, args.visual_preview]):
        console.print("[yellow]No trimming operation specified. Use --preview to view episode info.[/yellow]")
        args.preview = True
    
    # Visual preview requires interface
    if args.visual_preview and not args.interface:
        console.print("[red]Error: --visual-preview requires --interface[/red]")
        return 1
    
    try:
        # Initialize interface if needed for visual preview
        interface = None
        if args.visual_preview:
            console.print("[cyan]Initializing robot connection for visual preview...[/cyan]")
            interface = G1Interface(args.interface, use_motion_switcher=True)
            interface.initialize()
        
        # Initialize trimmer
        data_manager = DataManager()
        trimmer = EpisodeTrimmer(data_manager, interface)
        
        # Load episode
        trimmer.load_episode(episode_path)
        
        # Show preview
        trimmer.preview_episode()
        
        if args.preview and not any([args.trim_start, args.trim_end, args.start_time, args.end_time]):
            return 0
        
        if args.visual_preview and not any([args.trim_start, args.trim_end, args.start_time, args.end_time]):
            # Visual preview without any trimming - just preview original episode
            trimmer.visual_preview(playback_speed=0.5)
            return 0
        
        # Apply trimming operations
        console.print("\n[bold cyan]Applying Trimming Operations[/bold cyan]")
        
        if args.start_time is not None or args.end_time is not None:
            # Time-based trimming
            if args.preview:
                trimmer.trim_time_range(args.start_time, args.end_time, dry_run=True)
            else:
                trimmer.trim_time_range(args.start_time, args.end_time)
        else:
            # Frame-based trimming
            if args.trim_start:
                if args.preview:
                    trimmer.trim_start(args.trim_start, dry_run=True)
                else:
                    trimmer.trim_start(args.trim_start)
            
            if args.trim_end:
                if args.preview:
                    trimmer.trim_end(args.trim_end, dry_run=True)
                else:
                    trimmer.trim_end(args.trim_end)
        
        if args.preview:
            console.print("\n[yellow]Preview mode - no changes saved[/yellow]")
            return 0
        
        # Visual preview of trimmed episode (before saving)
        if args.visual_preview:
            console.print("\n[cyan]Visual preview of trimmed episode...[/cyan]")
            trimmer.visual_preview(playback_speed=0.5)
            
            if not Confirm.ask("\n[bold]Save the trimmed episode?[/bold]", default=True):
                console.print("[yellow]Trimmed episode not saved[/yellow]")
                return 0
        
        # Validate
        trimmer.validate_episode()
        
        # Save
        trimmer.save_trimmed(
            output_path=args.output,
            backup=not args.no_backup,
            overwrite=True
        )
        
        console.print("\n[bold green]✓ Episode trimmed successfully![/bold green]")
        
        # Update config if this was a note
        if args.note:
            config = MusicConfig.load(args.instrument)
            # Reload episode to get updated metadata
            episode_data = data_manager.load_episode(episode_path)
            config.update_note_episode(
                args.note,
                episode_path,
                episode_data['metadata']['duration'],
                episode_data['metadata']['frequency']
            )
            config.save()
            console.print(f"[green]✓ Updated configuration for note {args.note}[/green]")
        
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

