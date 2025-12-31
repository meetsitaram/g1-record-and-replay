# 🎉 G1 Record and Replay - Setup Complete!

## Summary

The **g1-record-and-replay** repository has been fully implemented with all requested features:

✅ **Calibrate Mode** - Discover and save joint limits  
✅ **Record Mode** - Capture trajectories with passive motors  
✅ **Replay Mode** - Execute recorded motions with safety features  
✅ **Visualization** - Plot joint trajectories  
✅ **Network Interface** - Cross-referenced with `g1_upload.py` for compatibility  

---

## What Was Built

### Core Components

1. **`g1_record_replay/core/g1_interface.py`**
   - Low-level SDK wrapper matching `g1_upload.py` pattern
   - Dual mode: read-only (calibration) vs control mode (recording/replay)
   - Simple state subscription with callback handlers
   - Command publishing for motor control

2. **`g1_record_replay/core/data_manager.py`**
   - HDF5-based episode storage
   - JSON calibration data
   - Episode listing and management

3. **`g1_record_replay/calibrate.py`**
   - Live terminal display with min/max tracking
   - Joint group filtering (arms/legs/waist/all)
   - Interactive controls (R: reset, S: save, Q: quit)

4. **`g1_record_replay/record.py`**
   - Passive motor mode (freely movable)
   - High-frequency recording (default 50 Hz)
   - Real-time frame counter and statistics

5. **`g1_record_replay/replay.py`**
   - Smooth 3-second transition to start position
   - Pause/resume capability
   - Safety confirmation prompt
   - Speed control (0.25x to 2.0x)

### CLI Scripts

- `scripts/calibrate.py` - Calibration entry point
- `scripts/record.py` - Recording entry point
- `scripts/replay.py` - Replay entry point
- `scripts/visualize_episode.py` - Plot trajectories
- `tests/test_connection.py` - Connection tester

### Documentation

- `README.md` - Main documentation
- `QUICKSTART.md` - Step-by-step getting started guide
- `IMPLEMENTATION_NOTES.md` - Technical details and design decisions
- `config/default_config.yaml` - Configuration reference

---

## Key Design Updates (Based on g1_upload.py)

After cross-referencing with your working `g1_upload.py` script, the implementation was updated to:

1. **Match network interface handling exactly**
   - Same `ChannelFactoryInitialize(0, network_interface)` pattern
   - Support for common names: `eth0`, `enp2s0`, etc.

2. **Smart motion switcher usage**
   - Calibration: Read-only mode (no motion switcher) ← Like g1_upload.py
   - Recording: Control mode (for passive motor setting)
   - Replay: Control mode (for trajectory execution)

3. **Simple state subscription**
   - Direct callback pattern matching g1_upload.py
   - Clean separation of read vs control operations

---

## Quick Start

### 1. Install
```bash
cd ~/projects/g1-piano/g1-record-and-replay
pip3 install -e .
```

### 2. Test Connection
```bash
python tests/test_connection.py --network-interface eth0
```

### 3. Calibrate
```bash
python scripts/calibrate.py --network-interface eth0 --joint-group arms
```

### 4. Record
```bash
python scripts/record.py --network-interface eth0 --name "my_motion" --frequency 50
```

### 5. Replay
```bash
python scripts/replay.py --network-interface eth0 --episode data/episodes/episode_001.h5 --speed 1.0
```

### 6. Visualize
```bash
python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --joint-group arms
```

---

## File Structure

```
g1-record-and-replay/
├── README.md                    # Main documentation
├── QUICKSTART.md               # Getting started guide
├── IMPLEMENTATION_NOTES.md     # Technical details
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
├── config/
│   ├── default_config.yaml    # Default settings
│   └── joint_limits.json      # Calibration data (generated)
├── g1_record_replay/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── g1_interface.py    # Robot interface (✓ matches g1_upload.py pattern)
│   │   └── data_manager.py    # Episode storage
│   ├── calibrate.py           # Calibration logic
│   ├── record.py              # Recording logic
│   └── replay.py              # Replay logic
├── scripts/
│   ├── calibrate.py           # CLI: calibration
│   ├── record.py              # CLI: recording
│   ├── replay.py              # CLI: replay
│   └── visualize_episode.py   # CLI: visualization
├── tests/
│   └── test_connection.py     # Connection test
└── data/
    └── episodes/              # Recorded episodes (generated)
```

---

## Dependencies

All standard packages:
- `numpy` - Array operations
- `h5py` - Episode storage
- `pyyaml` - Config files
- `rich` - Beautiful terminal UI
- `matplotlib` - Trajectory plotting
- `unitree_sdk2_python` - Robot SDK (already installed)

---

## Safety Features

✅ **Calibration**: Pure read-only, no motor commands  
✅ **Recording**: Motors in passive mode (Kp=0, Kd=0)  
✅ **Replay**: User confirmation + smooth transition + emergency stop  

---

## Network Interface Compatibility

The implementation uses the same network interface pattern as `g1_upload.py`:

```python
# Both scripts use this pattern:
ChannelFactoryInitialize(0, network_interface)
ChannelSubscriber("rt/lowstate", LowState_)
```

**Common interface names:**
- `eth0` - Primary Ethernet
- `enp2s0` - Alternative Ethernet naming
- `wlan0` - WiFi (if available)

Check with: `ip a` or `ifconfig`

---

## Next Steps

1. **Test the connection:**
   ```bash
   python tests/test_connection.py --network-interface eth0
   ```

2. **Try calibration** (safe, read-only):
   ```bash
   python scripts/calibrate.py --network-interface eth0 --joint-group arms
   ```

3. **Record a simple motion** (e.g., arm wave):
   ```bash
   python scripts/record.py --network-interface eth0 --name "arm_wave"
   ```

4. **Visualize the recording:**
   ```bash
   python scripts/visualize_episode.py --list
   python scripts/visualize_episode.py --episode data/episodes/<your_episode>.h5
   ```

5. **Replay at slow speed first:**
   ```bash
   python scripts/replay.py --network-interface eth0 --episode data/episodes/<your_episode>.h5 --speed 0.5
   ```

---

## Support Files

- **QUICKSTART.md** - Detailed walkthrough with examples
- **IMPLEMENTATION_NOTES.md** - Technical design decisions
- **README.md** - Full API documentation

---

## What's Different from g1_upload.py

| Feature | g1_upload.py | g1-record-and-replay |
|---------|--------------|---------------------|
| Purpose | Read state → Upload to server | Record/replay trajectories |
| State reading | ✓ Same pattern | ✓ Same pattern |
| Network init | ✓ Same | ✓ Same |
| Motor control | ✗ None | ✓ Optional (when needed) |
| Data storage | ✗ Uploads to server | ✓ Local HDF5 files |

---

## Repository Status

🎯 **All features implemented and ready for testing!**

The repository is fully functional and follows best practices observed from your working `g1_upload.py` script. All operations are motor-joint focused as requested (no camera/sensor data).

Start with the test script to verify your robot connection, then proceed with calibration before recording/replay.

Happy robot programming! 🤖

