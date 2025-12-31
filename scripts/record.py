#!/usr/bin/env python3
"""CLI entry point for recording mode"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from g1_record_replay.record import run_recording


def main():
    parser = argparse.ArgumentParser(
        description="Record G1 robot joint trajectories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record arms only (default, SAFE)
  python scripts/record.py --network-interface enp2s0 --name "arm_motion"

  # Record with custom frequency (still arms only)
  python scripts/record.py --network-interface enp2s0 --name "pick_cup" --frequency 50

  # Record with live joint position display
  python scripts/record.py --network-interface enp2s0 --name "test" --show-positions

  # Record ALL joints (WARNING: includes legs!)
  python scripts/record.py --network-interface enp2s0 --joint-group all --name "full_motion"

Controls during recording:
  S - Stop and save recording
  C - Cancel without saving
        """
    )
    
    parser.add_argument(
        '--network-interface',
        type=str,
        default=None,
        help='Network interface connected to robot (e.g., enp2s0)'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Name/description for the episode'
    )
    
    parser.add_argument(
        '--frequency',
        type=float,
        default=50.0,
        help='Recording frequency in Hz (default: 50.0)'
    )
    
    parser.add_argument(
        '--joint-group',
        type=str,
        choices=['all', 'arms', 'legs', 'waist'],
        default='arms',
        help='Which joints to record (default: arms, SAFE - only arms move)'
    )
    
    parser.add_argument(
        '--show-positions',
        action='store_true',
        help='Display current joint positions in real-time during recording'
    )
    
    args = parser.parse_args()
    
    # Run recording
    run_recording(
        network_interface=args.network_interface,
        frequency=args.frequency,
        episode_name=args.name,
        joint_group=args.joint_group,
        show_positions=args.show_positions
    )


if __name__ == '__main__':
    main()

