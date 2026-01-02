#!/usr/bin/env python3
"""CLI entry point for replay mode"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from g1_record_replay.replay import run_replay


def main():
    parser = argparse.ArgumentParser(
        description="Replay recorded G1 robot trajectories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Replay at normal speed
  python scripts/replay.py --network-interface enp2s0 --episode data/episodes/episode_001.h5

  # Replay at half speed
  python scripts/replay.py --network-interface enp2s0 --episode data/episodes/episode_001.h5 --speed 0.5

  # Replay at double speed
  python scripts/replay.py --network-interface enp2s0 --episode data/episodes/episode_001.h5 --speed 2.0

Controls during replay:
  P - Pause/resume playback
  Q - Quit safely
  
Safety:
  - System will prompt for confirmation before starting
  - 3-second smooth transition to start position
  - Emergency stop with Ctrl+C
        """
    )
    
    parser.add_argument(
        '--network-interface',
        type=str,
        default=None,
        help='Network interface connected to robot (e.g., enp2s0)'
    )
    
    parser.add_argument(
        '--episode',
        type=str,
        required=True,
        help='Path to episode file to replay'
    )
    
    parser.add_argument(
        '--speed',
        type=float,
        default=1.0,
        help='Playback speed multiplier (0.25 to 2.0, default: 1.0)'
    )
    
    parser.add_argument(
        '--skip-safety',
        action='store_true',
        help='Skip safety confirmation prompt (NOT RECOMMENDED - for testing only)'
    )
    
    args = parser.parse_args()
    
    # Validate episode file exists
    episode_path = Path(args.episode)
    if not episode_path.exists():
        print(f"Error: Episode file not found: {args.episode}")
        sys.exit(1)
    
    # Run replay
    run_replay(
        network_interface=args.network_interface,
        episode_path=str(episode_path),
        playback_speed=args.speed,
        skip_safety=args.skip_safety
    )


if __name__ == '__main__':
    main()

