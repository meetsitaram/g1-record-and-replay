#!/usr/bin/env python3
"""CLI entry point for calibration mode"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from g1_record_replay.calibrate import run_calibration


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate G1 robot joint limits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calibrate all joints
  python scripts/calibrate.py --network-interface enp2s0

  # Calibrate only arms
  python scripts/calibrate.py --network-interface enp2s0 --joint-group arms

  # Calibrate legs only
  python scripts/calibrate.py --network-interface enp2s0 --joint-group legs

Controls during calibration:
  R - Reset min/max values
  S - Save calibration and exit
  Q - Quit without saving
        """
    )
    
    parser.add_argument(
        '--network-interface',
        type=str,
        default=None,
        help='Network interface connected to robot (e.g., enp2s0)'
    )
    
    parser.add_argument(
        '--joint-group',
        type=str,
        choices=['all', 'arms', 'legs', 'waist'],
        default='all',
        help='Which joint group to calibrate (default: all)'
    )
    
    args = parser.parse_args()
    
    # Run calibration
    run_calibration(
        network_interface=args.network_interface,
        joint_group=args.joint_group
    )


if __name__ == '__main__':
    main()

