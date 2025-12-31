# Recording Arms While Standing - Safety Summary

## ✅ Your Question Answered

**Q:** "I would like to have zeroTorque mode just for the arms when recording, but do not interfere with the other motors. Can that be done?"

**A:** **YES! This is already implemented and working correctly.**

---

## How It Works

### During Recording (Default: Arms Only)

```bash
python scripts/record.py --network-interface enp2s0 --name "test"
```

**What happens to each motor group:**

| Motor Group | Indices | Count | State During Recording | Effect |
|-------------|---------|-------|------------------------|--------|
| **Arms** | 15-28 | 14 | ✅ **PASSIVE** (zero torque) | Free to move by hand |
| **Legs** | 0-11 | 12 | ✅ **ACTIVE** (unchanged) | Keep robot standing |
| **Waist** | 12-14 | 3 | ✅ **ACTIVE** (unchanged) | Maintain torso position |

**Result:** Robot stays standing, arms move freely. **Exactly what you wanted!** ✓

---

## Technical Details

### The Implementation

The `set_passive_mode(joint_indices)` function in `g1_interface.py` only affects specified motors:

```python
def set_passive_mode(self, joint_indices: Optional[list] = None):
    """Set ONLY specified motors to passive mode"""
    
    for i in joint_indices:  # ← Only these motors!
        self.low_cmd.motor_cmd[i].mode = 0    # Disable
        self.low_cmd.motor_cmd[i].kp = 0.0    # Zero position gain
        self.low_cmd.motor_cmd[i].kd = 0.0    # Zero velocity gain
        self.low_cmd.motor_cmd[i].tau = 0.0   # Zero torque
    
    # Other motors (not in joint_indices) are NOT modified!
    # They maintain their current state
```

### Key Difference from Global ZeroTorque

**Global ZeroTorque (FSM command):**
```python
loco_client.ZeroTorque()  # ❌ Affects ALL motors → Robot collapses
```

**Selective Passive Mode (Our implementation):**
```python
interface.set_passive_mode(joint_indices=[15,...,28])  # ✅ Only arms passive
```

---

## Verification

You can verify this works correctly:

### Option 1: Run the test script

```bash
python scripts/test_selective_passive.py
```

This shows which motors are affected for each joint group.

### Option 2: Try it on the robot

```bash
python scripts/record.py --network-interface enp2s0
```

**Observe:**
- ✅ Arms move freely when pushed
- ✅ Legs resist movement (still under control)
- ✅ Robot remains standing
- ✅ Waist maintains position

---

## Safety Benefits

### Why This is Safe

1. **Robot Stability**
   - Legs maintain torque → robot doesn't collapse
   - Waist maintains posture → torso stays upright
   - Only arms are passive → minimal impact on stability

2. **Predictable Behavior**
   - You know exactly which motors will be passive
   - Other motors won't suddenly lose torque
   - Robot behavior is predictable

3. **Natural Recording**
   - Similar to a person standing while moving arms
   - Can record natural arm motions
   - No need to support the robot externally

---

## Comparison Chart

| Scenario | Arms | Legs | Waist | Safe? | Use Case |
|----------|------|------|-------|-------|----------|
| **Record arms (default)** | Passive | Active | Active | ✅ **YES** | Standing robot |
| Record legs | Active | Passive | Active | ⚠️ **NO** | Robot will fall |
| Record all | Passive | Passive | Passive | ❌ **NO** | Only if lying down |
| Global ZeroTorque | Passive | Passive | Passive | ❌ **NO** | Robot collapses |

---

## Why We Updated Safety Checks

### Before

The safety checker would call `loco_client.ZeroTorque()` for all operations, which would disable ALL motors.

### After (Now)

- **Recording:** Safety check does NOT call `ZeroTorque()`
  - Only shows confirmation prompt
  - Lets `set_passive_mode(arms)` handle selective disabling
  - Legs stay active ✓

- **Replay:** Safety check DOES call `ZeroTorque()`
  - Replay needs full control, so FSM must be disabled
  - All motors will be commanded by replay
  - This is correct and safe ✓

---

## Updated Safety Message

When you run recording now, you'll see:

```
📹  RECORDING MODE SAFETY CHECK

About to record motion on: arms

This will:
  1. Set arms motors to PASSIVE mode (zero torque)
  2. These motors will move freely by hand
  3. Record joint positions as you move them
  4. Other motors (legs, waist) remain ACTIVE  ← This is the key!

Safety Notes:
  • Recording is safer than replay (selected motors are passive)
  • You can freely move the arms by hand
  • Other joints will maintain their current position
  • If recording arms: legs will keep the robot standing ✓

Ready to start recording? [Y/n]:
```

---

## Summary

✅ **Your concern is completely valid**  
✅ **The implementation already handles it correctly**  
✅ **Only specified motors (arms) go to zero torque**  
✅ **Other motors (legs, waist) remain active**  
✅ **Robot stays standing during arm recording**  

You can safely record arm motions while the robot is standing! 🎉

---

## References

- `SELECTIVE_MOTOR_CONTROL.md` - Full technical documentation
- `FSM_AND_SAFETY.md` - FSM vs low-level control
- `g1_interface.py` - Implementation of selective passive mode
- `scripts/test_selective_passive.py` - Verification script

