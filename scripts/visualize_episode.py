#!/usr/bin/env python3
"""CLI entry point for episode visualization"""

import argparse
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from g1_record_replay.core import DataManager, JOINT_NAMES


def plot_episode(episode_path: str, joint_indices: list = None, joint_names_filter: list = None, 
                 uniform_scale: bool = False, save_path: str = None, two_column: bool = False):
    """
    Plot joint trajectories from an episode.
    
    Args:
        episode_path: Path to episode file
        joint_indices: List of joint indices to plot (if None, plots all)
        joint_names_filter: List of joint names to plot (if None, uses joint_indices)
        uniform_scale: If True, use the same y-axis scale for all joints
        save_path: If provided, save plot to this path instead of showing
        two_column: If True, split into left/right columns for arm joints
    """
    # Load episode
    data_manager = DataManager()
    data = data_manager.load_episode(episode_path)
    
    joint_positions = data['joint_positions']
    timestamps = data['timestamps']
    metadata = data['metadata']
    
    # Determine which joints to plot
    if joint_names_filter:
        # Convert joint names to indices
        joint_indices = []
        for name in joint_names_filter:
            try:
                idx = JOINT_NAMES.index(name)
                joint_indices.append(idx)
            except ValueError:
                print(f"Warning: Unknown joint name '{name}', skipping")
    
    if joint_indices is None:
        joint_indices = list(range(29))  # Plot all joints
    
    num_joints = len(joint_indices)
    
    # Calculate global y-axis limits if uniform scale is requested
    y_min, y_max = None, None
    if uniform_scale:
        all_positions = joint_positions[:, joint_indices]
        y_min = np.min(all_positions)
        y_max = np.max(all_positions)
        # Add 5% padding
        y_range = y_max - y_min
        y_min -= y_range * 0.05
        y_max += y_range * 0.05
        print(f"Using uniform scale: [{y_min:.4f}, {y_max:.4f}] rad\n")
    
    # Print episode info
    print(f"\nEpisode: {metadata.get('episode_id', 'unknown')}")
    print(f"Duration: {metadata.get('duration', 0):.2f}s")
    print(f"Frames: {metadata.get('num_frames', 0)}")
    print(f"Frequency: {metadata.get('frequency', 0):.1f}Hz")
    if 'description' in metadata:
        print(f"Description: {metadata['description']}")
    print(f"\nPlotting {num_joints} joints...\n")
    
    # Split into left and right arms if two_column mode is enabled
    if two_column:
        # Separate left and right arm joints
        left_joints = [idx for idx in joint_indices if 'left' in JOINT_NAMES[idx].lower()]
        right_joints = [idx for idx in joint_indices if 'right' in JOINT_NAMES[idx].lower()]
        other_joints = [idx for idx in joint_indices if idx not in left_joints and idx not in right_joints]
        
        # Combine: left column gets left joints + half of others, right gets right joints + rest
        max_rows = max(len(left_joints), len(right_joints))
        
        # Create figure with two columns
        fig = plt.figure(figsize=(18, max_rows * 0.8))
        gs = GridSpec(max_rows, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        plot_layout = [(left_joints, 0), (right_joints, 1)]
    else:
        # Create single column figure
        fig = plt.figure(figsize=(14, min(12, num_joints * 0.8)))
        gs = GridSpec(num_joints, 1, figure=fig, hspace=0.3)
        plot_layout = [(joint_indices, None)]
    
    # Plot each joint
    for joints_list, col_idx in plot_layout:
        for i, joint_idx in enumerate(joints_list):
            # Determine subplot position
            if col_idx is None:
                # Single column layout
                ax = fig.add_subplot(gs[i, 0])
                is_last_in_column = (i == len(joints_list) - 1)
            else:
                # Two column layout
                ax = fig.add_subplot(gs[i, col_idx])
                is_last_in_column = (i == len(joints_list) - 1)
            
            joint_name = JOINT_NAMES[joint_idx]
            positions = joint_positions[:, joint_idx]
            
            # Calculate range of motion for this joint
            pos_min, pos_max = np.min(positions), np.max(positions)
            range_of_motion = pos_max - pos_min
            
            # Plot position
            ax.plot(timestamps, positions, 'b-', linewidth=1.5, label='Position')
            
            # Add velocity if available (only if not using uniform scale)
            if 'joint_velocities' in data and not uniform_scale:
                velocities = data['joint_velocities'][:, joint_idx]
                ax2 = ax.twinx()
                ax2.plot(timestamps, velocities, 'r-', linewidth=1.0, alpha=0.6, label='Velocity')
                ax2.set_ylabel('Velocity (rad/s)', color='r', fontsize=8)
                ax2.tick_params(axis='y', labelcolor='r')
            
            # Format
            ylabel = f'{joint_name}\n(rad)'
            if uniform_scale:
                # Add range info to label when using uniform scale
                ylabel += f'\nΔ={range_of_motion:.3f}'
            ax.set_ylabel(ylabel, fontsize=9)
            ax.grid(True, alpha=0.3)
            
            # Apply uniform scale if requested
            if uniform_scale and y_min is not None and y_max is not None:
                ax.set_ylim(y_min, y_max)
            
            # Only show x-label on bottom plot
            if is_last_in_column:
                ax.set_xlabel('Time (s)')
            else:
                ax.set_xticklabels([])
    
    # Title
    title = f"Episode: {metadata.get('episode_id', 'unknown')}"
    if 'description' in metadata:
        title += f" - {metadata['description']}"
    if uniform_scale:
        title += " [Uniform Scale]"
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved plot to: {save_path}")
    else:
        plt.show()


def list_episodes():
    """List all available episodes"""
    data_manager = DataManager()
    episodes = data_manager.list_episodes()
    
    if not episodes:
        print("No episodes found in data/episodes/")
        return
    
    print(f"\nFound {len(episodes)} episode(s):\n")
    
    for i, ep in enumerate(episodes, 1):
        print(f"{i}. {ep['filename']}")
        print(f"   ID: {ep['episode_id']}")
        print(f"   Duration: {ep['duration']:.2f}s, Frames: {ep['num_frames']}, Freq: {ep['frequency']:.1f}Hz")
        if 'description' in ep:
            print(f"   Description: {ep['description']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize recorded G1 robot trajectories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all episodes
  python scripts/visualize_episode.py --list

  # Plot episode (defaults: arms, uniform scale, two-column layout)
  python scripts/visualize_episode.py --episode data/episodes/episode_001.h5

  # Plot all joints instead of just arms
  python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --joint-group all

  # Plot only leg joints
  python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --joint-group legs

  # Disable uniform scale (auto-scale each joint independently)
  python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --no-uniform-scale

  # Use single column layout instead of two columns
  python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --no-two-column

  # Plot specific joints
  python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --joints "left_shoulder_pitch,left_elbow,right_shoulder_pitch"

  # Save plot to file
  python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --save output.png
        """
    )
    
    parser.add_argument(
        '--episode',
        type=str,
        help='Path to episode file to visualize'
    )
    
    parser.add_argument(
        '--joints',
        type=str,
        help='Comma-separated list of joint names to plot'
    )
    
    parser.add_argument(
        '--joint-group',
        type=str,
        choices=['all', 'arms', 'legs', 'waist'],
        default='arms',
        help='Plot a specific joint group (default: arms)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available episodes'
    )
    
    parser.add_argument(
        '--uniform-scale',
        action='store_true',
        default=True,
        help='Use the same y-axis scale for all joints to show relative magnitudes (default: True)'
    )
    
    parser.add_argument(
        '--no-uniform-scale',
        action='store_false',
        dest='uniform_scale',
        help='Disable uniform scale (auto-scale each joint independently)'
    )
    
    parser.add_argument(
        '--save',
        type=str,
        help='Save plot to file instead of displaying (e.g., output.png)'
    )
    
    parser.add_argument(
        '--two-column',
        action='store_true',
        default=True,
        help='Split into two columns (left arm | right arm) for larger plots (default: True)'
    )
    
    parser.add_argument(
        '--no-two-column',
        action='store_false',
        dest='two_column',
        help='Disable two-column layout (use single column)'
    )
    
    args = parser.parse_args()
    
    # List episodes if requested
    if args.list:
        list_episodes()
        return
    
    # Require episode if not listing
    if not args.episode:
        parser.error("--episode is required unless using --list")
    
    # Validate episode file
    episode_path = Path(args.episode)
    if not episode_path.exists():
        print(f"Error: Episode file not found: {args.episode}")
        sys.exit(1)
    
    # Determine which joints to plot
    joint_names_filter = None
    joint_indices = None
    
    if args.joints:
        joint_names_filter = [j.strip() for j in args.joints.split(',')]
    elif args.joint_group:
        joint_groups = {
            "legs": list(range(0, 12)),
            "waist": list(range(12, 15)),
            "arms": list(range(15, 29)),
            "all": list(range(29))
        }
        joint_indices = joint_groups[args.joint_group]
    
    # Plot episode
    plot_episode(
        episode_path=str(episode_path),
        joint_indices=joint_indices,
        joint_names_filter=joint_names_filter,
        uniform_scale=args.uniform_scale,
        save_path=args.save,
        two_column=args.two_column
    )


if __name__ == '__main__':
    main()

