# Safety Checklist - Before Using Record/Replay

## Quick Safety Verification

Before recording or replaying, verify these settings:

### ✅ Default Safety Settings

**Record Command:**
```bash
python scripts/record.py --network-interface enp2s0 --name "my_motion"
```

**Checklist:**
- [ ] No `--joint-group` specified (defaults to **arms**)
- [ ] OR explicitly has `--joint-group arms`
- [ ] Robot is standing/sitting in stable position
- [ ] Area around arms is clear of obstacles

**What will happen:**
- ✅ Arms: Will go passive (freely movable)
- ❌ Legs: Will stay active (robot stays standing)
- ❌ Waist: Will stay active (torso stays firm)

---

### ⚠️ Before Using `--joint-group all`

**ONLY use this if you explicitly want to control legs/waist:**
```bash
python scripts/record.py --network-interface enp2s0 --joint-group all --name "full_motion"
```

**Checklist:**
- [ ] Robot is in safe position (e.g., sitting or lying down)
- [ ] You are prepared for legs to go passive
- [ ] Support structure is in place if needed
- [ ] Emergency stop is accessible
- [ ] You understand legs will become freely movable

**What will happen:**
- ⚠️ Arms: Will go passive
- ⚠️ Legs: Will go passive (robot will collapse if standing!)
- ⚠️ Waist: Will go passive

---

## Default Settings Summary

| Operation | Default Joint Group | What Moves | Safe for Standing Robot? |
|-----------|-------------------|------------|-------------------------|
| **record.py** | **arms** | Only arms | ✅ YES |
| **replay.py** | (from recording) | Only arms* | ✅ YES |
| **calibrate.py** | (--joint-group parameter) | None (read-only) | ✅ YES |

*Replay uses whatever was recorded. If you recorded arms-only, replay will only move arms.

---

## Visual Safety Guide

### ✅ SAFE: Arms Only (Default)

```
        🤖 G1 Robot
        
    ✅ Arms         ❌ Head
       /|\            |
      / | \          / \
     🔓 | 🔓       🔒 | 🔒  
    /   |   \      ___🔒___
   /    |    \        |
  /     |     \       |
 /      |      \    🔒 🔒  ← Legs stay firm
/       |       \   |   |
        |          🔒  🔒
      🔒 🔒 ← Legs locked
        
Legend:
🔓 = Passive (freely movable)
🔒 = Active (stays in position)
```

### ⚠️ CAUTION: All Joints

```
        🤖 G1 Robot
        
    ⚠️ Arms        ⚠️ Waist
       /|\            |
      / | \          / \
     🔓 | 🔓       🔓 | 🔓  
    /   |   \      ___🔓___
   /    |    \        |
  /     |     \       |
 /      |      \    🔓 🔓  ← Legs go passive!
/       |       \   |   |
        |          🔓  🔓  ← Robot may collapse!
      ⚠️ ⚠️ ← ALL passive!
        
⚠️ Robot will collapse if standing!
```

---

## Command Examples

### ✅ Safe Commands (Arms Only)

```bash
# Record arms (default - SAFE)
python scripts/record.py --network-interface enp2s0 --name "wave"

# Explicitly specify arms (same as above)
python scripts/record.py --network-interface enp2s0 --joint-group arms --name "wave"

# Replay (uses joint group from recording)
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/wave.h5

# Calibrate arms
python scripts/calibrate.py --network-interface enp2s0 --joint-group arms
```

### ⚠️ Potentially Unsafe Commands (Require Extra Care)

```bash
# Record ALL joints (includes legs!)
python scripts/record.py --network-interface enp2s0 --joint-group all --name "full"

# Record legs only (robot will collapse if standing!)
python scripts/record.py --network-interface enp2s0 --joint-group legs --name "leg_motion"
```

---

## Pre-Flight Checklist

Before each recording session:

### Physical Setup
- [ ] Robot is in stable position
- [ ] Workspace around arms is clear
- [ ] Emergency stop button is accessible
- [ ] Network connection is stable

### Command Verification
- [ ] Command does NOT have `--joint-group all` (unless intended)
- [ ] OR command explicitly has `--joint-group arms`
- [ ] Episode name is descriptive
- [ ] Network interface is correct

### Mental Checklist
- [ ] I know which joints will move
- [ ] I am prepared to press emergency stop if needed
- [ ] I have tested connection with test script
- [ ] I have calibrated the joints I'm recording

---

## What to Do If Something Goes Wrong

### During Recording
1. **Press `Ctrl+C`** - Stops recording immediately
2. Check robot is stable
3. Review what went wrong

### During Replay
1. **Press `Q`** - Safe quit
2. **Press `Ctrl+C`** - Emergency stop
3. Robot will automatically set motors to passive on exit

---

## Verification Commands

### Check what's in an episode file:
```bash
python scripts/visualize_episode.py --list
python scripts/visualize_episode.py --episode data/episodes/my_episode.h5
```

### Test connection before recording:
```bash
python tests/test_connection.py --network-interface enp2s0
```

---

## Final Safety Rules

1. ✅ **Always use default (arms only)** unless you have a specific reason
2. ✅ **Test with slow movements first** before complex motions
3. ✅ **Clear the workspace** around the arms
4. ✅ **Have emergency stop ready** (Ctrl+C or physical e-stop)
5. ⚠️ **Never use `--joint-group all`** while robot is standing
6. ⚠️ **Always verify joint group** in episode metadata before replay

---

## Quick Reference Card

**Copy and paste these safe commands:**

```bash
# 1. Test connection
python tests/test_connection.py --network-interface enp2s0

# 2. Calibrate arms
python scripts/calibrate.py --network-interface enp2s0 --joint-group arms

# 3. Record arms (SAFE)
python scripts/record.py --network-interface enp2s0 --name "arm_motion"

# 4. Visualize
python scripts/visualize_episode.py --list

# 5. Replay
python scripts/replay.py --network-interface enp2s0 --episode data/episodes/<your_file>.h5 --speed 0.5
```

**Remember: Default is ARMS ONLY = SAFE** ✅

