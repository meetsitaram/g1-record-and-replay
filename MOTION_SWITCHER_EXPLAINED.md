# Motion Switcher - Detailed Explanation

## What is the Motion Switcher?

The **MotionSwitcherClient** is a **control mode management system** built into the Unitree robot's operating system. Think of it as an **arbitrator** that decides who gets to control the robot's motors at any given time.

## Why Does It Exist?

The Unitree G1 robot can run multiple control programs simultaneously:
- **High-level sport mode** (walking, balancing, autonomous navigation)
- **Low-level motor control** (direct joint commands from your code)
- **Built-in behaviors** (AI mode, normal mode, advanced mode)
- **App control** (via Unitree's mobile app)

**Problem:** If multiple programs try to send motor commands at the same time, the robot would receive conflicting instructions and could behave dangerously!

**Solution:** The Motion Switcher acts as a **gatekeeper** - only ONE control mode can be active at a time.

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────┐
│         Unitree Robot Operating System      │
│                                             │
│  ┌────────────────────────────────────┐   │
│  │     Motion Switcher Service        │   │
│  │  (running on robot's computer)     │   │
│  └────────────────────────────────────┘   │
│                   ↕                         │
│    ┌──────────────┴──────────────┐        │
│    │   Motor Control System       │        │
│    │   (sends actual commands)    │        │
│    └──────────────┬──────────────┘        │
│                   ↓                         │
│         [ Physical Motors ]                 │
└─────────────────────────────────────────────┘
         ↑         ↑          ↑
         │         │          │
    Your Code   Sport Mode   App
```

### Key Concepts

1. **Service-based**: It's an RPC (Remote Procedure Call) service running on the robot
2. **Exclusive Access**: Only ONE mode can "own" motor control at a time
3. **Must Release**: Programs must properly release control when done

---

## API Methods

The MotionSwitcherClient provides three main operations:

### 1. `CheckMode()`
**Purpose:** Check what control mode is currently active

```python
status, result = msc.CheckMode()
# result = {'name': 'sport_mode'}  # if sport mode is active
# result = {'name': ''}            # if nothing is active (free)
```

**Use case:** Before taking control, check if someone else is using the robot

### 2. `SelectMode(name)`
**Purpose:** Request control of the robot

```python
# Built-in modes you can select:
msc.SelectMode("normal")    # Normal walking mode
msc.SelectMode("advanced")  # Advanced movement mode
msc.SelectMode("ai")        # AI mode
```

**Use case:** Switch the robot to a specific built-in behavior mode

### 3. `ReleaseMode()`
**Purpose:** Give up control of the robot

```python
msc.ReleaseMode()
# Now others can take control
```

**Use case:** When your program is done, release control so others can use the robot

---

## When Do You Need It?

### ✅ **Need Motion Switcher** (Active Control)

You need the Motion Switcher when you want to:
- **Send motor commands** to move the robot
- **Override built-in behaviors**
- **Take exclusive control** of motors

**Examples:**
- Low-level motor control (like our replay mode)
- Setting motors to passive mode (like our record mode)
- Custom walking gaits
- Manipulation tasks

**Why:** You're actively controlling motors → need exclusive access

### ❌ **DON'T Need Motion Switcher** (Passive Observation)

You don't need it when you're only:
- **Reading robot state** (joint positions, IMU, battery)
- **Monitoring** without sending commands
- **Logging data** to files or servers

**Examples:**
- Our calibration mode (just reading positions)
- Your `g1_upload.py` script (just reading and uploading)
- Data collection scripts
- Visualization tools

**Why:** You're not sending commands → no conflict possible

---

## How We Use It in g1-record-and-replay

### Calibration (Read-Only)
```python
# NO motion switcher needed
interface = G1Interface(network_interface, use_motion_switcher=False)
interface.initialize()
state = interface.get_joint_state()  # Just reading
```

**Why:** We're only subscribing to `rt/lowstate` to read positions. No commands sent.

### Recording (Passive Motors)
```python
# YES, motion switcher needed
interface = G1Interface(network_interface, use_motion_switcher=True)
interface.initialize()  # This checks and releases existing modes
interface.set_passive_mode()  # Sends commands to disable motors
```

**Why:** Even though motors become passive, we still send the command to make them passive. That requires exclusive access.

### Replay (Active Control)
```python
# YES, motion switcher needed
interface = G1Interface(network_interface, use_motion_switcher=True)
interface.initialize()  # Acquires control
interface.send_joint_commands(positions)  # Sends commands
```

**Why:** We're actively sending motor position commands. Definitely needs exclusive access.

---

## What Happens During Initialization

When `use_motion_switcher=True`, here's what happens:

```python
# 1. Initialize the client
self.msc = MotionSwitcherClient()
self.msc.SetTimeout(5.0)
self.msc.Init()

# 2. Check if anyone else is controlling the robot
status, result = self.msc.CheckMode()

# 3. If someone is (like sport_mode), kick them off
while result.get('name'):
    print(f"Releasing existing mode: {result.get('name')}")
    self.msc.ReleaseMode()
    status, result = self.msc.CheckMode()
    time.sleep(1)

# 4. Now we have exclusive control!
```

**Important:** This is why you might see "Releasing existing mode: sport_mode" when starting - we're politely asking the sport mode to step aside so we can take control.

---

## Common Issues & Solutions

### Issue 1: "Another program is controlling the robot"
**Symptoms:** Your commands don't work, or you get errors
**Cause:** Sport mode (from app) or another program has control
**Solution:** 
```python
msc.ReleaseMode()  # Release any existing control
```

### Issue 2: "Robot becomes unresponsive after my program crashes"
**Symptoms:** App won't work, robot won't respond
**Cause:** Your program crashed without calling `ReleaseMode()`
**Solution:**
```python
# Run this standalone to release control:
msc = MotionSwitcherClient()
msc.Init()
msc.ReleaseMode()
```

### Issue 3: "I just want to read data, do I need this?"
**Answer:** No! If you're only reading (like `g1_upload.py`), you don't need the motion switcher at all.

---

## Best Practices

### ✅ DO:
- Always release control when done (use `try/finally`)
- Check current mode before taking control
- Use motion switcher only when actually controlling motors
- Keep control time minimal (don't hog it)

### ❌ DON'T:
- Don't use motion switcher for read-only operations
- Don't forget to release (leaves robot in bad state)
- Don't fight with other programs (coordinate control)
- Don't assume you have control (always check first)

---

## Comparison with g1_upload.py

Your `g1_upload.py` script is a **perfect example** of when you **DON'T** need the motion switcher:

```python
# g1_upload.py approach (read-only)
ChannelFactoryInitialize(0, network_interface)
sub_low = ChannelSubscriber("rt/lowstate", LowState_)
sub_low.Init(LowStateHandler, 10)
# Just reading state → No motion switcher needed!
```

This is much simpler and can run alongside other programs without conflicts.

---

## Summary

**Motion Switcher = Control Permission System**

| Scenario | Need Motion Switcher? | Why |
|----------|---------------------|-----|
| Read joint positions | ❌ No | Just observing |
| Upload data to server | ❌ No | Just observing |
| Send motor commands | ✅ Yes | Actively controlling |
| Set motors passive | ✅ Yes | Sending command (even if passive) |
| Record trajectory | ✅ Yes | Need to set passive mode |
| Replay trajectory | ✅ Yes | Sending position commands |
| Calibrate (just reading) | ❌ No | Just observing |

**Key Takeaway:** 
- If you're **reading** data → No motion switcher needed (like `g1_upload.py`)
- If you're **writing** commands → Yes, need motion switcher

This is why our implementation has the `use_motion_switcher` flag - it lets us be efficient (no motion switcher for calibration) while being safe (require it for control operations).

