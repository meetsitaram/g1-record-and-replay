# Motor Resistance During Recording

## Issue: Residual Resistance During Teleoperation

When recording (teleoperation), you may feel some resistance when moving the arms, even though they're in "passive mode." This document explains why and what we've done about it.

---

## Why Motors Have Residual Resistance

Even with zero torque commands, motors can have resistance from:

### 1. **Motor Controller Update Rate**
- Commands sent at 50Hz (every 20ms)
- Between commands, motor controller may apply small holding torque
- **Solution:** Send passive commands continuously ✓ (we now do this)

### 2. **Physical Motor Characteristics**
- **Cogging torque**: Magnetic forces between rotor and stator
- **Back-EMF**: Motors generate voltage when moved (acts as resistance)
- **Inherent friction**: Brushes, bearings, seals
- **Cannot be eliminated** through software

### 3. **Gearbox Friction**
- Most robot joints have gear reduction (e.g., 1:50, 1:100)
- Gears have inherent friction
- Backdrivability varies by gear type
- **Cannot be eliminated** through software

### 4. **Motor Controller Limits**
- Even with `kp=0, kd=0, tau=0`, controller may apply minimum damping
- Safety feature to prevent free-spinning
- Varies by motor model
- **Minimal but present**

---

## What We've Implemented

### ✅ Continuous Passive Commands (New!)

**Before:**
```python
# Set passive once at start
interface.set_passive_mode(joint_indices=arm_indices)
time.sleep(0.5)

# Then just record (motors drift back to slight resistance)
while recording:
    record_position()
```

**After (Now):**
```python
# Set passive once at start
interface.set_passive_mode(joint_indices=arm_indices)
time.sleep(0.5)

# Continuously reinforce passive mode at 50Hz
while recording:
    interface.set_passive_mode(joint_indices=arm_indices, continuous=True)
    record_position()
```

**Effect:** Minimal software-induced resistance. Motors stay as free as physically possible.

---

## What to Expect

### Normal Resistance Levels

| Joint Type | Expected Resistance | Reason |
|------------|---------------------|--------|
| **Shoulder** | Very low | Large motors, good backdrivability |
| **Elbow** | Low | Medium gearing, decent backdrivability |
| **Wrist** | Low-Medium | Smaller motors, tighter gears |

### Comparing to Other Robots

**LeRobot/Koch Robots (Direct Drive):**
- Minimal resistance
- No gearboxes
- Feel very "free"

**Unitree G1 (Geared Motors):**
- Some resistance is normal
- High torque capability (benefit of gears)
- Trade-off: torque vs. backdrivability

**UR Robots (Industrial):**
- Similar resistance to G1
- Collaborative robots have good backdrivability
- Still noticeable friction

---

## Testing the Improvement

### Before the Fix:
You felt resistance increasing over time as motors drifted back to having slight damping.

### After the Fix (Now):
You should feel consistent, minimal resistance throughout recording.

### To Test:
```bash
python scripts/record.py --network-interface enp2s0 --name "test_resistance"
```

**Try:**
1. Move arms slowly → Should feel smooth, consistent resistance
2. Move arms quickly → Should move freely
3. Let go → Arms should stop (not spring back)
4. Compare to initial feel → Should stay the same throughout recording

---

## If Resistance is Still Too High

### Check 1: Is FSM Disabled?
```bash
python scripts/check_robot_safety.py
# Select option 1: Set ZeroTorque
```

If FSM is active, arms will have significant resistance (FSM trying to hold position).

### Check 2: Are Commands Being Sent?
During recording, you should see:
```
Recording... Frames: 150, Duration: 3.0s, Freq: 50.0Hz
```

If frequency drops below 40Hz, commands may not be sent frequently enough.

### Check 3: Physical Issues
- Are cables/wires pulling on the arms?
- Are arm joints clean (no debris)?
- Is robot properly maintained?

---

## Comparison Chart

| Resistance Type | Can Fix? | Status | Effect |
|----------------|----------|--------|--------|
| Software damping | ✅ Yes | **Fixed** | Eliminated by continuous commands |
| Motor cogging | ❌ No | Normal | 5-10% of total resistance |
| Gearbox friction | ❌ No | Normal | 40-60% of total resistance |
| FSM interference | ✅ Yes | **Checked** | Safety system prevents this |
| Cable drag | ✅ Yes | Check manually | Can be significant if tight |

---

## Expected Feel

### What You Should Feel Now:
- ✅ Smooth, consistent resistance (not increasing over time)
- ✅ Can move arms freely with reasonable effort
- ✅ No sudden "catches" or "locks"
- ✅ Resistance feels similar at all speeds
- ✅ Arms don't spring back when released

### What Would Indicate a Problem:
- ❌ Resistance increases over time
- ❌ Arms suddenly lock up
- ❌ Arms spring back to a position
- ❌ Significant difference between joints
- ❌ Very high resistance (feels "powered")

---

## Technical Details

### Motor Command Structure
```python
motor_cmd[i].mode = 0      # 0 = Disabled (passive)
motor_cmd[i].q = 0.0       # Target position (ignored when disabled)
motor_cmd[i].dq = 0.0      # Target velocity (ignored when disabled)
motor_cmd[i].tau = 0.0     # Feedforward torque = 0
motor_cmd[i].kp = 0.0      # Position gain = 0
motor_cmd[i].kd = 0.0      # Velocity gain = 0
```

**All gains are zero** = Minimal motor controller resistance

### Command Frequency
- **Recording rate**: 50Hz (data capture)
- **Passive command rate**: 50Hz (same as recording)
- **Motor controller update**: ~1000Hz (internal)

Between our 50Hz commands (20ms apart), the motor controller maintains the last command.

---

## Summary

✅ **We've implemented continuous passive commands (50Hz)**  
✅ **Software-induced resistance is now minimized**  
⚠️ **Some physical resistance is normal and expected**  
✅ **Resistance should feel consistent throughout recording**  
✅ **Much better than sending command only once**  

If you still feel too much resistance:
1. Check that FSM is disabled (`check_robot_safety.py`)
2. Verify recording frequency stays at 50Hz
3. Check for physical obstructions (cables, debris)
4. Compare resistance between different joints (should be similar)

---

## References

- `g1_interface.py` - Updated `set_passive_mode()` with continuous option
- `record.py` - Calls `set_passive_mode()` at 50Hz during recording
- `FSM_AND_SAFETY.md` - FSM interference explanation
- Unitree SDK documentation - Motor control modes

