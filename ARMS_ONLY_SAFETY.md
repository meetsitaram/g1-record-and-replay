# ✅ Arms-Only Safety Features Implemented

## Summary

The record and replay system has been updated with **joint group filtering** to ensure only specified joints (like arms) are affected, preventing any unwanted movement of legs or other motors.

---

## What Was Changed

### 1. Core Interface (`g1_interface.py`)

**Added:**
- `JOINT_GROUPS` dictionary defining joint groups
- `get_joint_indices(group)` function to get indices for a group
- `joint_indices` parameter to `set_passive_mode()`
- `joint_indices` parameter to `send_joint_commands()`

**Joint Groups:**
```python
JOINT_GROUPS = {
    "legs": [0-11],    # 12 joints
    "waist": [12-14],  # 3 joints
    "arms": [15-28],   # 14 joints (7 per arm)
    "all": [0-28]      # All 29 joints
}
```

### 2. Record Mode (`record.py`)

**Added:**
- `joint_group` parameter (default: "arms")
- Only sets specified joints to passive mode
- Stores `joint_group` and `joint_indices` in episode metadata

**Before (UNSAFE):**
```python
# Would set ALL 29 motors passive
self.interface.set_passive_mode()
```

**After (SAFE):**
```python
# Only sets arm motors passive
self.interface.set_passive_mode(joint_indices=self.joint_indices)
```

### 3. Replay Mode (`replay.py`)

**Added:**
- Reads `joint_group` and `joint_indices` from episode metadata
- Only commands the joints that were recorded
- Shows which joint group is being replayed

**Before (UNSAFE):**
```python
# Would command ALL 29 motors
self.interface.send_joint_commands(positions)
```

**After (SAFE):**
```python
# Only commands arm motors
self.interface.send_joint_commands(positions, joint_indices=self.joint_indices)
```

### 4. CLI Scripts

**record.py:**
```bash
# NEW: --joint-group parameter (default: arms)
python scripts/record.py --network-interface enp2s0 --joint-group arms
```

---

## How It Works

### Recording Arms Only

```bash
python scripts/record.py --network-interface enp2s0 --joint-group arms --name "arm_motion"
```

**What happens:**
1. ✅ **Only arm motors (15-28) set to passive**
2. ❌ Leg motors (0-11) remain active/locked
3. ❌ Waist motors (12-14) remain active/locked
4. ✅ You can freely move the arms
5. ✅ Episode saves `joint_group: "arms"` in metadata

### Replaying Arms Only

```bash
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/arm_motion.h5
```

**What happens:**
1. ✅ Loads episode and reads `joint_group: "arms"` from metadata
2. ✅ **Only sends commands to arm motors (15-28)**
3. ❌ **No commands sent to legs or waist**
4. ✅ Other motors stay in their current position
5. ✅ Safe replay of only the recorded joints

---

## Joint Index Reference

| Joint Group | Indices | Count | Description |
|-------------|---------|-------|-------------|
| **legs** | 0-11 | 12 | Both legs (hips, knees, ankles) |
| **waist** | 12-14 | 3 | Waist yaw, roll, pitch |
| **arms** | 15-28 | 14 | Both arms (shoulders, elbows, wrists) |
| **all** | 0-28 | 29 | All motors |

### Detailed Arm Joints (15-28):
```
Left Arm (15-21):
  15: left_shoulder_pitch
  16: left_shoulder_roll
  17: left_shoulder_yaw
  18: left_elbow
  19: left_wrist_roll
  20: left_wrist_pitch
  21: left_wrist_yaw

Right Arm (22-28):
  22: right_shoulder_pitch
  23: right_shoulder_roll
  24: right_shoulder_yaw
  25: right_elbow
  26: right_wrist_roll
  27: right_wrist_pitch
  28: right_wrist_yaw
```

---

## Safety Verification

### Test 1: Check what joints are affected

```python
from g1_record_replay.core import get_joint_indices

arms = get_joint_indices('arms')
print(f"Arms: {arms}")
# Output: [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]

# Verify NO leg joints
assert all(i >= 15 for i in arms), "Arms should not include leg joints (0-11)"
assert all(i <= 28 for i in arms), "Arms should not exceed joint count"
```

### Test 2: Verify episode metadata

After recording, check the episode file:
```python
from g1_record_replay.core import DataManager

dm = DataManager()
data = dm.load_episode("data/episodes/your_episode.h5")
print(f"Joint group: {data['metadata']['joint_group']}")
print(f"Joint indices: {data['metadata']['joint_indices']}")
```

Should show:
```
Joint group: arms
Joint indices: [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
```

---

## Usage Examples

### Example 1: Record Arms Only (DEFAULT)
```bash
python scripts/record.py --network-interface enp2s0 --name "wave"
# --joint-group defaults to 'arms'
```

### Example 2: Record with Explicit Arms
```bash
python scripts/record.py --network-interface enp2s0 --name "wave" --joint-group arms
```

### Example 3: Record All Joints (if needed)
```bash
python scripts/record.py --network-interface enp2s0 --name "full_motion" --joint-group all
```

### Example 4: Record Legs Only (if needed)
```bash
python scripts/record.py --network-interface enp2s0 --name "walk" --joint-group legs
```

---

## Safety Guarantees

✅ **When recording with `--joint-group arms`:**
- Leg motors: ❌ Not affected (stay in current position)
- Waist motors: ❌ Not affected (stay in current position)
- Arm motors: ✅ Set to passive (freely movable)

✅ **When replaying an arms-only episode:**
- Leg motors: ❌ No commands sent (stay in current position)
- Waist motors: ❌ No commands sent (stay in current position)
- Arm motors: ✅ Commands sent (replay the motion)

✅ **Metadata ensures safety:**
- Episode file stores which joints were recorded
- Replay automatically uses only those joints
- No risk of accidentally commanding wrong joints

---

## Before This Fix

**❌ UNSAFE - Would affect ALL motors:**
```bash
python scripts/record.py --network-interface enp2s0
# Would set ALL 29 motors passive (legs would go limp!)

python scripts/replay.py --network-interface enp2s0 --episode file.h5
# Would command ALL 29 motors (legs would move!)
```

## After This Fix

**✅ SAFE - Only affects specified joints:**
```bash
python scripts/record.py --network-interface enp2s0 --joint-group arms
# Only sets 14 arm motors passive (legs stay firm!)

python scripts/replay.py --network-interface enp2s0 --episode file.h5
# Only commands 14 arm motors (legs stay still!)
```

---

## Verification Checklist

Before using record/replay in production:

- [ ] Verify `--joint-group arms` is set (or defaults to arms)
- [ ] Check episode metadata after recording shows `joint_group: "arms"`
- [ ] Test record mode: only arms should be freely movable
- [ ] Test replay mode: only arms should move
- [ ] Confirm legs stay in place during both record and replay

---

## Technical Details

### How passive mode works
```python
# Old code (UNSAFE):
for i in range(29):  # ALL motors
    self.low_cmd.motor_cmd[i].mode = 0  # Disable

# New code (SAFE):
for i in joint_indices:  # ONLY specified motors
    self.low_cmd.motor_cmd[i].mode = 0  # Disable
```

### How replay commands work
```python
# Old code (UNSAFE):
for i in range(29):  # ALL motors
    self.low_cmd.motor_cmd[i].q = positions[i]

# New code (SAFE):
for i in joint_indices:  # ONLY specified motors
    self.low_cmd.motor_cmd[i].q = positions[i]
```

---

## Summary

🎯 **Goal:** Ensure only arms move during record/replay  
✅ **Solution:** Joint group filtering at core level  
🛡️ **Safety:** Metadata tracks which joints to control  
📝 **Default:** `--joint-group arms` for all operations  

**You can now safely record and replay arm motions without affecting legs or waist!** 🦾

