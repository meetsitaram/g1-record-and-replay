"""Data Manager - Handle episode storage and loading"""

import os
import json
import h5py
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class DataManager:
    """Manages episode data storage and retrieval"""
    
    def __init__(self, episodes_dir: str = "data/episodes"):
        """
        Initialize data manager.
        
        Args:
            episodes_dir: Directory to store episode files
        """
        self.episodes_dir = Path(episodes_dir)
        self.episodes_dir.mkdir(parents=True, exist_ok=True)
    
    def save_episode(self,
                    joint_positions: np.ndarray,
                    timestamps: np.ndarray,
                    joint_velocities: Optional[np.ndarray] = None,
                    metadata: Optional[Dict[str, Any]] = None,
                    episode_name: Optional[str] = None) -> str:
        """
        Save episode data to HDF5 file.
        
        Args:
            joint_positions: Joint positions array (num_frames, 29)
            timestamps: Timestamps array (num_frames,)
            joint_velocities: Joint velocities array (num_frames, 29), optional
            metadata: Dictionary of metadata (description, operator, etc.)
            episode_name: Name for the episode (auto-generated if None)
            
        Returns:
            Path to saved episode file
        """
        # Generate episode ID and filename
        if episode_name:
            # Sanitize episode name
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in episode_name)
            episode_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        else:
            episode_id = f"episode_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = self.episodes_dir / f"{episode_id}.h5"
        
        # Validate data shapes
        num_frames = len(timestamps)
        if joint_positions.shape[0] != num_frames:
            raise ValueError(f"Position frames ({joint_positions.shape[0]}) != timestamps ({num_frames})")
        if joint_velocities is not None and joint_velocities.shape[0] != num_frames:
            raise ValueError(f"Velocity frames ({joint_velocities.shape[0]}) != timestamps ({num_frames})")
        
        # Calculate statistics
        duration = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0.0
        avg_frequency = num_frames / duration if duration > 0 else 0.0
        
        # Prepare metadata
        full_metadata = {
            "episode_id": episode_id,
            "timestamp": datetime.now().isoformat(),
            "num_frames": num_frames,
            "duration": float(duration),
            "frequency": float(avg_frequency),
            "num_joints": joint_positions.shape[1],
        }
        
        if metadata:
            full_metadata.update(metadata)
        
        # Save to HDF5
        with h5py.File(filepath, 'w') as f:
            # Store data arrays
            f.create_dataset('joint_positions', data=joint_positions, compression='gzip')
            f.create_dataset('timestamps', data=timestamps, compression='gzip')
            
            if joint_velocities is not None:
                f.create_dataset('joint_velocities', data=joint_velocities, compression='gzip')
            
            # Store metadata as attributes
            for key, value in full_metadata.items():
                f.attrs[key] = value
        
        print(f"Episode saved: {filepath}")
        print(f"  Frames: {num_frames}, Duration: {duration:.2f}s, Freq: {avg_frequency:.1f}Hz")
        
        return str(filepath)
    
    def load_episode(self, filepath: str) -> Dict[str, Any]:
        """
        Load episode data from HDF5 file.
        
        Args:
            filepath: Path to episode file
            
        Returns:
            Dictionary containing:
                - joint_positions: (num_frames, 29) array
                - timestamps: (num_frames,) array
                - joint_velocities: (num_frames, 29) array (if available)
                - metadata: dict of metadata
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Episode file not found: {filepath}")
        
        with h5py.File(filepath, 'r') as f:
            # Load data
            data = {
                'joint_positions': f['joint_positions'][:],
                'timestamps': f['timestamps'][:],
            }
            
            # Load velocities if available
            if 'joint_velocities' in f:
                data['joint_velocities'] = f['joint_velocities'][:]
            
            # Load metadata
            metadata = {}
            for key in f.attrs.keys():
                metadata[key] = f.attrs[key]
            data['metadata'] = metadata
        
        return data
    
    def list_episodes(self) -> List[Dict[str, Any]]:
        """
        List all available episodes with metadata.
        
        Returns:
            List of dictionaries containing episode info
        """
        episodes = []
        
        for filepath in sorted(self.episodes_dir.glob("*.h5")):
            try:
                with h5py.File(filepath, 'r') as f:
                    info = {
                        'filepath': str(filepath),
                        'filename': filepath.name,
                        'episode_id': f.attrs.get('episode_id', 'unknown'),
                        'num_frames': f.attrs.get('num_frames', 0),
                        'duration': f.attrs.get('duration', 0.0),
                        'frequency': f.attrs.get('frequency', 0.0),
                        'timestamp': f.attrs.get('timestamp', 'unknown'),
                    }
                    
                    # Add description if available
                    if 'description' in f.attrs:
                        info['description'] = f.attrs['description']
                    
                    episodes.append(info)
            except Exception as e:
                print(f"Warning: Could not read {filepath}: {e}")
        
        return episodes
    
    def save_calibration(self, joint_limits: Dict[str, Dict[str, float]], 
                        filepath: str = "config/joint_limits.json"):
        """
        Save joint calibration limits to JSON file.
        
        Args:
            joint_limits: Dictionary mapping joint names to {min, max, index, name}
            filepath: Path to save calibration file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        calibration_data = {
            "calibration_date": datetime.now().isoformat(),
            "robot_model": "G1-29DOF",
            "joints": joint_limits
        }
        
        with open(filepath, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        
        print(f"Calibration saved: {filepath}")
    
    def load_calibration(self, filepath: str = "config/joint_limits.json") -> Optional[Dict[str, Any]]:
        """
        Load joint calibration limits from JSON file.
        
        Args:
            filepath: Path to calibration file
            
        Returns:
            Calibration data dictionary or None if not found
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return data
    
    def delete_episode(self, filepath: str):
        """
        Delete an episode file.
        
        Args:
            filepath: Path to episode file to delete
        """
        filepath = Path(filepath)
        if filepath.exists():
            filepath.unlink()
            print(f"Deleted episode: {filepath}")
        else:
            print(f"Episode not found: {filepath}")

