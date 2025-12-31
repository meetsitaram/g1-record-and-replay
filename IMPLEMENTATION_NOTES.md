# Implementation Notes

## Network Interface Handling

The implementation has been updated to match the pattern used in `g1_upload.py` for consistency and reliability.

### Key Design Decisions

#### 1. **Network Interface Parameter**
- Follows the same pattern as `g1_upload.py`
- Uses `ChannelFactoryInitialize(0, network_interface)`
- Supports common interface names: `eth0`, `enp2s0`, etc.
- Can be omitted for default behavior

#### 2. **Motion Switcher Usage**
The interface now has two modes based on whether control is needed:

**Read-Only Mode** (`use_motion_switcher=False`):
- Used for: Calibration
- Only subscribes to robot state
- No `MotionSwitcherClient` initialization
- Simpler, more lightweight
- Pattern matches `g1_upload.py`

**Control Mode** (`use_motion_switcher=True`):
- Used for: Recording (passive mode), Replay (active control)
- Initializes `MotionSwitcherClient` for robot control
- Can publish commands via `rt/lowcmd`
- Required for any motor control operations

### Usage Examples

```python
# Read-only (calibration)
interface = G1Interface(network_interface="eth0", use_motion_switcher=False)
interface.initialize()
state = interface.get_joint_state()

# Control mode (recording/replay)
interface = G1Interface(network_interface="eth0", use_motion_switcher=True)
interface.initialize()
interface.set_passive_mode()  # For recording
# or
interface.send_joint_commands(positions)  # For replay
```

### Comparison with g1_upload.py

| Feature | g1_upload.py | Our Implementation |
|---------|--------------|-------------------|
| Network init | `ChannelFactoryInitialize(0, interface)` | ✓ Same |
| State subscription | `ChannelSubscriber("rt/lowstate", LowState_)` | ✓ Same |
| Callback pattern | Simple callback function | ✓ Same (wrapped in class) |
| Motion control | N/A (read-only) | Optional via `use_motion_switcher` |
| Command publishing | N/A | Only when `use_motion_switcher=True` |

### Error Handling

- Timeout after 10 seconds if no state received
- Clear error messages for initialization failures
- Graceful shutdown even if passive mode fails

### Network Interface Tips

Common interface names:
- `eth0` - Typical Ethernet on robot
- `enp2s0` - Common on development machines
- `wlan0` - WiFi (if available)

To find your interface: `ip a` or `ifconfig`

## Data Format

### Episode Storage (HDF5)
- Positions: `(num_frames, 29)` float64
- Velocities: `(num_frames, 29)` float64 (optional)
- Timestamps: `(num_frames,)` float64
- Metadata: HDF5 attributes

### Calibration Storage (JSON)
```json
{
  "calibration_date": "ISO timestamp",
  "robot_model": "G1-29DOF",
  "joints": {
    "joint_name": {
      "min": float,
      "max": float,
      "index": int,
      "name": string
    }
  }
}
```

## Safety Features

1. **Calibration**: Pure read-only, no commands sent
2. **Recording**: Motors set to passive (Kp=0, Kd=0, mode=0)
3. **Replay**: 
   - User confirmation required
   - 3-second smooth transition to start
   - Emergency stop (Ctrl+C) at any time
   - Pause/resume capability

## Performance

- State reading: ~500 Hz (native SDK rate)
- Recording: 50-100 Hz recommended
- Replay: 500 Hz command rate
- Memory: ~1-2 MB per minute of recording (50 Hz)

## Known Limitations

1. Currently only supports joint position/velocity (no IMU, no BMS)
2. No real-time constraints (soft real-time via Python)
3. Network latency affects control quality
4. No trajectory smoothing/filtering

## Future Enhancements

Potential additions:
- [ ] IMU data recording
- [ ] BMS/battery data recording  
- [ ] Trajectory smoothing/filtering
- [ ] Real-time playback visualization
- [ ] Multi-robot support
- [ ] ROS2 bridge
- [ ] Web interface for episode management

