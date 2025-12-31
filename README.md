# G1 Record and Replay

A Python toolkit for recording and replaying motor joint trajectories on the Unitree G1 robot.

## ⚠️ SAFETY NOTICE

**By default, all operations are limited to ARMS ONLY (joints 15-28).**

- ✅ **Record**: Only arm motors set to passive (legs stay firm)
- ✅ **Replay**: Only arm motors commanded (legs don't move)
- ⚠️ **To control other joints**: Must explicitly specify `--joint-group all/legs/waist`

See `ARMS_ONLY_SAFETY.md` for complete safety documentation.

## Features

- **Calibrate**: Discover and save joint limits by manually moving the robot
- **Record**: Capture joint trajectories with motors in passive mode
- **Replay**: Execute recorded trajectories on the robot

## Installation

### Prerequisites
- Python >= 3.8
- Unitree SDK2 Python (requires cyclonedds)
- Network connection to G1 robot
- `uv` package manager (recommended)

### Quick Setup (Automated)
```bash
cd ~/projects/g1-piano/g1-record-and-replay
./setup_dependencies.sh
```

This script will:
1. Install cyclonedds (if not present)
2. Install unitree_sdk2_python
3. Install g1-record-and-replay
4. Test all imports

### Manual Installation

1. **Setup cyclonedds** (required by unitree SDK):
```bash
cd ~
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir -p build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install
export CYCLONEDDS_HOME="$HOME/cyclonedds/install"
```

2. **Install unitree SDK**:
```bash
cd ~/projects/g1-piano/unitree_sdk2_python
uv pip install -e .
```

3. **Install g1-record-and-replay**:
```bash
cd ~/projects/g1-piano/g1-record-and-replay
uv pip install -e .
```

**Note:** Add `export CYCLONEDDS_HOME="$HOME/cyclonedds/install"` to your `~/.bashrc` or `~/.zshrc`

## Quick Connection Check

Before using the robot, verify the connection:

```bash
python scripts/check_g1_connection.py
```

This script will:
- ✅ Detect active network interfaces
- ✅ Check if robot is reachable (ping test)
- ✅ Test SDK connection
- ✅ Show which interface to use

## Usage

### 1. Calibrate Joint Limits
Manually move the robot joints to their limits while the system records min/max positions:

```bash
python scripts/calibrate.py --network-interface enp2s0 --joint-group arms
```

Options:
- `--network-interface`: Network interface connected to robot (e.g., enp2s0)
- `--joint-group`: Which joints to calibrate: `all`, `arms`, `legs`, `waist` (default: all)

Controls:
- `R`: Reset min/max values
- `S`: Save calibration to file
- `Q`: Quit without saving

### 2. Record a Trajectory
Record robot movements with motors in passive mode (freely movable):

```bash
# SAFE: Records arms only (default)
python scripts/record.py --network-interface enp2s0 --name "arm_motion"

# With custom frequency (still arms only)
python scripts/record.py --network-interface enp2s0 --name "pick_cup" --frequency 50
```

Options:
- `--network-interface`: Network interface connected to robot
- `--name`: Episode name/description
- `--frequency`: Recording frequency in Hz (default: 50)
- `--joint-group`: Which joints to record (default: **arms** - SAFE)

Controls:
- `S`: Stop and save recording
- `C`: Cancel without saving

### 3. Replay a Trajectory
Replay a recorded episode on the robot:

```bash
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/episode_001.h5 --speed 1.0
```

Options:
- `--network-interface`: Network interface connected to robot
- `--episode`: Path to episode file
- `--speed`: Playback speed multiplier (default: 1.0)

Controls:
- `P`: Pause/resume
- `Q`: Quit safely

### 4. Visualize Episodes
Plot joint trajectories from a recorded episode:

```bash
python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --joints "left_shoulder_pitch,left_elbow"
```

## Safety

- **Calibrate**: Read-only mode, no commands sent to motors
- **Record**: Motors in passive mode, no active control
- **Replay**: 
  - Warning prompt before execution
  - 3-second smooth transition to start position
  - Emergency stop with Ctrl+C
  - Position/velocity limits enforced

## Project Structure

```
g1-record-and-replay/
├── config/              # Configuration and calibration data
├── data/episodes/       # Recorded episodes
├── g1_record_replay/    # Main package
│   ├── core/           # Core functionality
│   ├── calibrate.py    # Calibration logic
│   ├── record.py       # Recording logic
│   └── replay.py       # Replay logic
└── scripts/            # CLI entry points
```

## Data Format

Episodes are stored in HDF5 format with the following structure:
- `joint_positions`: (num_frames, 29) array of joint angles
- `joint_velocities`: (num_frames, 29) array of joint velocities
- `timestamps`: (num_frames,) array of timestamps
- Metadata: episode_id, duration, frequency, description

## License

MIT License

