# Selective Motor Control - Arms Only Recording

## Overview

The G1 record-and-replay system supports **selective motor control**, allowing you to disable specific joint groups (like arms) while leaving others (like legs) active.

## How It Works

### Recording Mode (Arms Only - Default)

When you record with `--joint-group arms`:

```bash
python scripts/record.py --network-interface enp2s0 --name "test"
```

**What happens:**

1. ✅ **ARM motors (14 joints)** → Set to PASSIVE (zero torque)
   - Left/right shoulder (pitch, roll, yaw)
   - Left/right elbow
   - Left/right wrist (roll, pitch, yaw)
   - **These motors move freely by hand**

2. ✅ **LEG motors (12 joints)** → **REMAIN ACTIVE** (unchanged)
   - Continue maintaining their current position
   - Keep the robot standing/balanced
   - **Not affected by the recording operation**

3. ✅ **WAIST motors (3 joints)** → **REMAIN ACTIVE** (unchanged)
   - Continue maintaining torso position
   - **Not affected by the recording operation**

### Technical Implementation

The `set_passive_mode(joint_indices)` function in `g1_interface.py`:

```python
def set_passive_mode(self, joint_indices: Optional[list] = None):
    """
    Set motors to passive mode (zero torque, free movement).
    Only affects specified motors!
    """
    # ... initialization ...
    
    # Only set SPECIFIED motors to passive
    for i in joint_indices:  # ← Only these motors!
        self.low_cmd.motor_cmd[i].mode = 0  # Disable
        self.low_cmd.motor_cmd[i].kp = 0.0  # Zero position gain
        self.low_cmd.motor_cmd[i].kd = 0.0  # Zero velocity gain
        self.low_cmd.motor_cmd[i].tau = 0.0 # Zero torque
    
    # Other motors (not in joint_indices) are NOT modified
```

**Key Point:** Only the motors in `joint_indices` are modified. Other motors continue with their previous state.

---

## Motor Groups

### Arms Group (indices 15-28, 14 motors)

```
Left Arm:
  15: left_shoulder_pitch
  16: left_shoulder_roll
  17: left_shoulder_yaw
  18: left_elbow
  19: left_wrist_roll
  20: left_wrist_pitch
  21: left_wrist_yaw

Right Arm:
  22: right_shoulder_pitch
  23: right_shoulder_roll
  24: right_shoulder_yaw
  25: right_elbow
  26: right_wrist_roll
  27: right_wrist_pitch
  28: right_wrist_yaw
```

### Legs Group (indices 0-11, 12 motors)

```
Left Leg:
  0-5: Hip, knee, ankle joints

Right Leg:
  6-11: Hip, knee, ankle joints
```

### Waist Group (indices 12-14, 3 motors)

```
12-14: Waist yaw, roll, pitch
```

---

## Use Cases

### ✅ Safe: Recording Arms While Standing

```bash
python scripts/record.py \
  --network-interface enp2s0 \
  --joint-group arms \
  --name "arm_motion"
```

**Result:**
- Arms are free to move (zero torque)
- Legs keep robot standing
- Safe and stable

### ✅ Safe: Recording One Arm (Coming Soon)

```python
# Custom script for left arm only
from g1_record_replay import G1Interface

interface = G1Interface(network_interface="enp2s0", use_motion_switcher=True)
interface.initialize()

# Only left arm joints (15-21)
left_arm_indices = list(range(15, 22))
interface.set_passive_mode(joint_indices=left_arm_indices)

# Right arm (22-28) and legs remain active!
```

### ⚠️ Caution: Recording All Motors

```bash
python scripts/record.py \
  --network-interface enp2s0 \
  --joint-group all \
  --name "full_body"
```

**Result:**
- ALL motors go passive
- Robot will collapse if not supported
- **Only use when robot is lying down or externally supported!**

---

## Safety Benefits

### Why Selective Control is Important

1. **Robot Stability**
   - Legs remain active → robot stays standing
   - No risk of collapse during arm recording

2. **Operator Safety**
   - Only manipulating arms
   - Legs won't suddenly move
   - Predictable behavior

3. **Natural Recording**
   - Can record arm motions naturally
   - Robot mimics human-like recording setup
   - Similar to a person standing still while moving their arms

---

## Comparison with Full ZeroTorque

### ❌ Global ZeroTorque (Don't use for standing robot!)

```python
loco_client.ZeroTorque()  # FSM command
```

**Effect:** ALL motors lose torque → Robot collapses!

### ✅ Selective Passive Mode (Our Implementation)

```python
interface.set_passive_mode(joint_indices=[15, 16, 17, ...])  # Low-level command
```

**Effect:** Only specified motors lose torque → Other motors maintain position!

---

## Verification

To verify selective control is working:

1. **Start recording arms:**
```bash
python scripts/record.py --network-interface enp2s0
```

2. **Observe:**
   - ✅ Arms move freely when you push them
   - ✅ Legs resist movement (still have torque)
   - ✅ Robot remains standing
   - ✅ Safety message confirms: "Other motors (legs, waist) remain ACTIVE"

3. **Try to move legs:**
   - They should resist (still under control)
   - They won't move freely like the arms

---

## Advanced: Custom Joint Selection

You can record any subset of joints:

```python
from g1_record_replay import G1Interface, DataManager

interface = G1Interface(network_interface="enp2s0", use_motion_switcher=True)
interface.initialize()

# Example: Only elbows and wrists (18, 19, 20, 21, 25, 26, 27, 28)
elbow_wrist_indices = [18, 19, 20, 21, 25, 26, 27, 28]

# Set only these motors to passive
interface.set_passive_mode(joint_indices=elbow_wrist_indices)

# Record positions...
# Shoulders (15-17, 22-24) remain active!
```

---

## Summary

| Operation | Arms | Legs | Waist | Robot State |
|-----------|------|------|-------|-------------|
| Record arms (default) | PASSIVE ✓ | ACTIVE ✓ | ACTIVE ✓ | Standing ✓ |
| Record all | PASSIVE ⚠️ | PASSIVE ⚠️ | PASSIVE ⚠️ | Collapses ⚠️ |
| Global ZeroTorque | PASSIVE ❌ | PASSIVE ❌ | PASSIVE ❌ | Collapses ❌ |

**Recommendation:** Always use `--joint-group arms` (the default) when recording standing robots!

---

## References

- `g1_interface.py` - Implementation of `set_passive_mode()`
- `record.py` - Recording with selective motor control
- `FSM_AND_SAFETY.md` - FSM vs low-level control
- `SAFETY_CHECKLIST.md` - Safety procedures

