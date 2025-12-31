# FSM (Finite State Machine) and Safety Guide

## ⚠️ Critical Safety Concept: High-Level vs Low-Level Control

### The Problem

The Unitree G1 robot operates in two control modes that **must not conflict**:

#### 1. **High-Level Mode (FSM Active)**
- Robot's built-in controller is running
- FSM (Finite State Machine) sends commands to maintain posture/balance
- Motors actively maintain positions for standing, walking, etc.
- **Arms may have active torque** to hold positions
- **Legs are actively balancing** the robot

#### 2. **Low-Level Mode (Direct Motor Control)**
- Your code sends position/velocity/torque commands directly to motors
- No built-in behaviors - you have full control
- FSM should be **disabled** (set to ZeroTorque or Damp)

### ⚠️ THE DANGER

**If you send low-level commands while FSM is active:**
- ❌ Two control systems fight for the same motors
- ❌ Robot receives conflicting commands
- ❌ Results in **jerky, rough movements**
- ❌ Can cause **sudden high torque**
- ❌ Risk of **motor damage**
- ❌ Risk of **mechanical stress**
- ❌ **SAFETY HAZARD** to people nearby

**This is what you heard about - sending low-level commands while the robot is in "high state" causes rough behavior!**

---

## FSM States (IDs)

The FSM can be in different states, controlled by `SetFsmId()`:

| FSM ID | State | Description | Safe for Low-Level? |
|--------|-------|-------------|---------------------|
| **0** | **ZeroTorque** | All motors have zero torque, completely passive | ✅ **YES - SAFEST** |
| **1** | **Damp** | Low damping mode, minimal resistance | ✅ **YES** |
| 2 | Squat | Robot squats down | ❌ NO |
| 3 | Sit | Robot sits | ❌ NO |
| 4 | StandUp | Robot stands up from squat | ❌ NO |
| 200 | Start | High-level locomotion active | ❌ NO |
| 500+ | Various Walking/Movement States | Active locomotion | ❌ NO |

**Key Takeaway:** Always set FSM to **0 (ZeroTorque)** or **1 (Damp)** before low-level control!

---

## How to Use Safely

### Option 1: Automated Safety (Recommended)

Our code now includes **automatic safety checks**:

```bash
# Record mode (automatically disables motors in the specified group)
python scripts/record.py --network-interface enp2s0

# Replay mode (automatically checks FSM and disables it)
python scripts/replay.py --episode data/episodes/episode.h5 --network-interface enp2s0
```

The safety checker will:
1. ✅ Show you what will happen
2. ✅ Ask for confirmation
3. ✅ Disable FSM automatically
4. ✅ Verify safety before proceeding

### Option 2: Manual Safety Check

Run the safety checker manually:

```bash
python scripts/check_robot_safety.py
```

This tool lets you:
- Check current robot state
- Manually set ZeroTorque mode
- Manually set Damp mode
- Verify readiness for low-level control

### Option 3: Programmatic Control

In your own code:

```python
from g1_record_replay import SafetyChecker

# Create safety checker
checker = SafetyChecker()

# Initialize and disable FSM
checker.initialize_loco_client()
checker.disable_fsm()  # Sets robot to ZeroTorque

# Now safe for low-level control
# ... your code here ...
```

---

## Safety Checklist Before Replay

Before running any replay operation:

- [ ] **FSM is disabled** (ZeroTorque or Damp mode)
- [ ] **Robot has clear space** to move
- [ ] **No one is touching** the robot
- [ ] **You are ready to press Ctrl+C** for emergency stop
- [ ] **Emergency stop is accessible**
- [ ] **You understand what joints will move**

---

## Understanding the LocoClient

The `LocoClient` is the high-level control interface that communicates with the robot's FSM:

```python
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

loco = LocoClient()
loco.SetTimeout(5.0)
loco.Init()

# Disable FSM (required before low-level control)
loco.ZeroTorque()  # Sets FSM ID to 0
loco.Damp()        # Sets FSM ID to 1

# High-level commands (when you want FSM active)
loco.Start()       # FSM ID 200 - start locomotion
loco.StandUp()     # FSM ID 4 - stand up
loco.Sit()         # FSM ID 3 - sit down
```

---

## What Happens During Record and Replay

### Recording Mode

```
1. Safety check asks for confirmation
2. Motors in specified group set to PASSIVE (zero torque)
   └─> This uses Motion Switcher + low-level commands
3. You can freely move motors by hand
4. Positions are recorded at 50Hz
5. Motors remain passive until program ends
```

**Recording is SAFE** - motors are passive, no active torque.

### Replay Mode

```
1. Safety check shows what will be controlled
2. User confirms it's safe
3. LocoClient.ZeroTorque() is called to disable FSM
   └─> This prevents conflict with low-level commands
4. Motion Switcher grants exclusive control
5. Low-level position commands are sent to motors
6. Motors actively move to replicate recording
```

**Replay is ACTIVE** - motors will move with force!

---

## Technical Details

### Why Two Control Systems?

1. **High-Level (FSM)**: Convenient for walking, balancing, built-in behaviors
2. **Low-Level**: Full control for custom movements, manipulation, research

Both are useful, but they **cannot run simultaneously** on the same joints!

### Control Flow

```
High-Level Control Path:
LocoClient → FSM Service → Motor Controller → Motors

Low-Level Control Path:
Your Code → DDS (rt/lowcmd) → Motor Controller → Motors

⚠️ CONFLICT if both paths are active!
```

### The Solution: Mode Switching

```python
# Before low-level control:
loco_client.ZeroTorque()  # Turn off high-level FSM
time.sleep(1.0)           # Wait for command to take effect

# Now safe to send low-level commands:
interface.send_joint_commands(positions)
```

---

## Troubleshooting

### "Robot is jerking/rough during replay"
**Cause:** FSM is still active  
**Solution:** Run `python scripts/check_robot_safety.py` and set ZeroTorque

### "Motors won't move during replay"
**Possible causes:**
1. FSM is preventing movement (set ZeroTorque)
2. Motion Switcher doesn't have control (check initialization)
3. Network connection issues (check `check_g1_connection.py`)

### "Safety check can't initialize LocoClient"
**Possible causes:**
1. Robot not connected to network
2. SDK not properly installed
3. Robot IP address not accessible

---

## References

- `g1_record_replay/safety.py` - Safety checker implementation
- `scripts/check_robot_safety.py` - Standalone safety tool
- `MOTION_SWITCHER_EXPLAINED.md` - Control permission system
- `SAFETY_CHECKLIST.md` - Complete safety procedures

---

## Summary

🔴 **Never send low-level commands while FSM is active**  
🟢 **Always call `ZeroTorque()` or `Damp()` before low-level control**  
🟢 **Use the built-in safety checks**  
🟢 **Verify robot state before operations**  

Stay safe and happy coding! 🤖

