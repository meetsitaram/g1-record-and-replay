# G1 Record and Replay - Quick Start Guide

This guide will help you get started with recording and replaying trajectories on your Unitree G1 robot.

## ⚠️ IMPORTANT SAFETY DEFAULT

**All record/replay operations default to ARMS ONLY.**

This means:
- ✅ Only the 14 arm motors (joints 15-28) will be affected
- ✅ Legs will NOT move or go passive
- ✅ Waist will NOT move or go passive
- ⚠️ Must explicitly use `--joint-group all` to control other joints

## Prerequisites

1. **Unitree G1 robot** with network connection
2. **Computer** connected to the robot via network
3. **Python 3.8+** installed
4. **unitree_sdk2_python** installed and working

## Installation

```bash
cd ~/projects/g1-piano/g1-record-and-replay
pip3 install -e .
```

## Step 1: Test Connection

First, verify that your computer can communicate with the robot:

```bash
python tests/test_connection.py --network-interface enp2s0
```

Replace `enp2s0` with your actual network interface name. If successful, you should see:
```
✓ Connection test passed!
```

## Step 2: Calibrate (Optional but Recommended)

Calibrate joint limits by manually moving the robot:

```bash
python scripts/calibrate.py --network-interface enp2s0 --joint-group arms
```

**During calibration:**
- Slowly move each joint to its maximum and minimum positions
- The system tracks and displays min/max values in real-time
- Press `R` to reset values if needed
- Press `S` to save when done
- Press `Q` to quit without saving

**Tip:** Start with just the arms to get familiar with the process.

## Step 3: Record a Trajectory

Record a movement by physically guiding the robot:

```bash
# DEFAULT: Arms only (SAFE)
python scripts/record.py --network-interface enp2s0 --name "wave_motion"
```

**During recording:**
- ✅ **Arm motors** are set to passive mode (freely movable)
- ❌ **Leg motors** stay active (robot stays standing)
- ❌ **Waist motors** stay active (torso stays firm)
- Move the robot arms through your desired motion
- The system records arm joint positions at 50 Hz
- Press `S` to stop and save
- Press `C` to cancel

**Example arm recordings to try:**
- Simple wave motion
- Reaching to different positions
- Sequential arm movements
- Grasping motions

**⚠️ WARNING: To record other joints, you MUST specify:**
```bash
python scripts/record.py --network-interface enp2s0 --joint-group all --name "full_motion"
```

## Step 4: Replay a Trajectory

Replay your recorded motion:

```bash
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/episode_001.h5 --speed 1.0
```

**During replay:**
- System will ask for confirmation (type `yes`)
- Robot smoothly transitions to start position (3 seconds)
- Motion replays at recorded speed
- Press `P` to pause/resume
- Press `Q` to quit safely
- Press `Ctrl+C` for emergency stop

**Safety tips:**
- Clear the area around the robot
- Start with slower speeds (--speed 0.5)
- Be ready to press Ctrl+C if needed
- Keep emergency stop accessible

## Step 5: Visualize (Optional)

View your recorded trajectories:

```bash
# List all episodes
python scripts/visualize_episode.py --list

# Plot all joints
python scripts/visualize_episode.py --episode data/episodes/episode_001.h5

# Plot only arms
python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --joint-group arms

# Plot specific joints
python scripts/visualize_episode.py --episode data/episodes/episode_001.h5 --joints "left_shoulder_pitch,left_elbow"
```

## Common Issues

### Connection Issues
**Problem:** "Failed to receive robot state"
**Solution:** 
- Check network cable connection
- Verify network interface name with `ip a`
- Ensure robot is powered on
- Check if other programs are using the SDK

### Recording Issues
**Problem:** Motors won't move freely
**Solution:**
- Check that recording mode properly set motors to passive
- Ensure no other control programs are running
- Try restarting the robot

### Replay Issues
**Problem:** Robot moves jerkily
**Solution:**
- Check recording frequency was high enough (50+ Hz)
- Ensure stable network connection
- Try slower playback speed

**Problem:** Robot won't move during replay
**Solution:**
- Verify motors are enabled
- Check that trajectory is valid
- Ensure smooth transition completed

## Workflow Examples

### Example 1: Simple Arm Wave
```bash
# 1. Calibrate arms
python scripts/calibrate.py --network-interface enp2s0 --joint-group arms

# 2. Record wave motion
python scripts/record.py --network-interface enp2s0 --name "arm_wave" --frequency 50

# 3. Visualize
python scripts/visualize_episode.py --episode data/episodes/<your_episode>.h5 --joint-group arms

# 4. Replay at slow speed first
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/<your_episode>.h5 --speed 0.5

# 5. Replay at normal speed
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/<your_episode>.h5 --speed 1.0
```

### Example 2: Full Body Motion
```bash
# 1. Calibrate everything
python scripts/calibrate.py --network-interface enp2s0 --joint-group all

# 2. Record full motion
python scripts/record.py --network-interface enp2s0 --name "full_body_motion" --frequency 50

# 3. Visualize all joints
python scripts/visualize_episode.py --episode data/episodes/<your_episode>.h5

# 4. Replay
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/<your_episode>.h5 --speed 1.0
```

## Tips for Best Results

1. **Recording Quality:**
   - Move slowly and smoothly during recording
   - Record at 50-100 Hz for smooth playback
   - Keep recordings short initially (5-10 seconds)
   - Practice the motion before recording

2. **Safety First:**
   - Always clear the area before replay
   - Start with slow playback speeds
   - Test in open space away from obstacles
   - Have emergency stop ready

3. **Calibration:**
   - Calibrate joints you plan to use
   - Move slowly during calibration
   - Ensure you reach actual limits
   - Re-calibrate if robot behavior changes

4. **Data Management:**
   - Use descriptive episode names
   - Visualize before replaying
   - Keep successful recordings
   - Delete failed attempts

## Next Steps

- Try recording more complex motions
- Experiment with different playback speeds
- Combine multiple recorded episodes
- Use recorded data for learning algorithms

## Getting Help

If you encounter issues:
1. Check the main README.md for detailed documentation
2. Run test_connection.py to verify setup
3. Check robot logs for error messages
4. Ensure SDK version is up to date

Happy recording! 🤖

