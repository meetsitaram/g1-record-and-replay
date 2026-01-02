# WiFi Connection to G1 Robot

## Overview

The G1 robot can be accessed via **WiFi** instead of ethernet. If your robot is accessible at a specific IP address (e.g., `100.96.120.54`), you need to identify which **network interface** on your computer is connected to that WiFi network.

## Why Interface Names, Not IP Addresses?

The Unitree SDK uses **DDS (Data Distribution Service)** for communication, which requires the **network interface name** (like `wlan0`, `wlp3s0`) rather than an IP address. The SDK uses this interface to:
1. Bind to the correct network adapter
2. Auto-discover the robot via DDS multicast
3. Establish bidirectional communication

## Quick Start

### Step 1: Find Your WiFi Interface

Use the new helper script:

```bash
python scripts/find_robot_interface.py --robot-ip 100.96.120.54
```

**Example Output:**
```
============================================================
G1 Robot Network Interface Finder
============================================================

🔍 Searching for interface that can reach 100.96.120.54...

Strategy 1: Checking subnet matches...
  ✓ wlan0 (100.96.120.10/24) - Same subnet!

============================================================
✅ Found interface: wlan0

The robot at 100.96.120.54 is reachable via: wlan0

Use this interface in your commands:
  python scripts/record.py --interface wlan0
  python scripts/replay.py --interface wlan0 --episode <file>
  python scripts/music/record_music.py --instrument piano --interface wlan0
============================================================
```

### Step 2: Use the Interface in Commands

Replace `--interface eth0` with your WiFi interface (e.g., `--interface wlan0`):

```bash
# Recording
python scripts/music/record_music.py --instrument piano --interface wlan0

# Playback
python scripts/music/play_music.py --instrument piano --interface wlan0 \
    --sequence "C1:left:quarter -> D1:left:quarter"

# Trimming with visual preview
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --visual-preview --interface wlan0
```

## Manual Interface Detection

### Option 1: List All Interfaces

```bash
python scripts/find_robot_interface.py --list-all
```

**Example Output:**
```
All available network interfaces:

  🔌 wlan0 (WiFi)
     IP: 100.96.120.10
     Netmask: /24

  🔌 eth0 (Ethernet)
     IP: 192.168.1.100
     Netmask: /24
```

### Option 2: Use System Commands

**Linux:**
```bash
# List all interfaces
ip addr show

# Or use ip link
ip link show
```

**Example Output:**
```
3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 100.96.120.10/24 brd 100.96.120.255 scope global dynamic wlan0
```

Look for the interface with an IP in the same subnet as the robot (`100.96.120.x`).

### Option 3: Test Connectivity

```bash
# Ping robot with specific interface
ping -I wlan0 100.96.120.54
```

If successful, `wlan0` is the correct interface!

## Common WiFi Interface Names

| System | Common Names |
|--------|-------------|
| **Ubuntu/Debian** | `wlan0`, `wlp3s0`, `wlx...` |
| **Arch Linux** | `wlan0`, `wlp...` |
| **Fedora/RHEL** | `wlan0`, `wlp...` |
| **USB WiFi** | `wlx...` (with MAC address) |

## Ethernet vs WiFi Comparison

| Aspect | Ethernet | WiFi |
|--------|----------|------|
| **Interface Name** | `eth0`, `enp2s0`, `ens33` | `wlan0`, `wlp3s0` |
| **Typical IP** | `192.168.123.x` | `100.96.120.x` (varies) |
| **Latency** | Lower (~1-2ms) | Higher (~5-20ms) |
| **Reliability** | More stable | Can have drops |
| **Speed** | 1 Gbps typical | 100-600 Mbps |
| **Best For** | High-frequency control | Recording, playback |

## Troubleshooting

### Can't Find Interface

**Problem:** `find_robot_interface.py` doesn't find any interface

**Solutions:**
1. **Verify robot connectivity:**
   ```bash
   ping 100.96.120.54
   ```
   
2. **Check you're on the right WiFi network**
   ```bash
   ip addr show | grep inet
   ```
   Look for an IP in `100.96.120.x` range

3. **List all interfaces manually:**
   ```bash
   python scripts/find_robot_interface.py --list-all
   ```

### Connection Timeout

**Problem:** Scripts timeout when connecting to robot

**Solutions:**
1. **Verify interface is correct:**
   ```bash
   ping -I wlan0 100.96.120.54
   ```

2. **Check firewall:**
   ```bash
   # Ubuntu/Debian
   sudo ufw status
   
   # If active, allow DDS ports
   sudo ufw allow from 100.96.120.0/24
   ```

3. **Try with different interface:**
   ```bash
   python scripts/check_g1_connection.py
   ```

### SDK Not Finding Robot

**Problem:** SDK initializes but can't find robot

**Solutions:**
1. **DDS uses multicast** - ensure multicast is enabled:
   ```bash
   # Check multicast route
   ip route show
   
   # Should see line like:
   # 224.0.0.0/4 dev wlan0 scope link
   ```

2. **Add multicast route if missing:**
   ```bash
   sudo ip route add 224.0.0.0/4 dev wlan0
   ```

3. **Check cyclonedds environment:**
   ```bash
   echo $CYCLONEDDS_HOME
   # Should point to: ~/cyclonedds/install
   ```

## Example Workflows

### First Time Setup with WiFi

```bash
# 1. Connect to robot's WiFi network
# (Use your system's WiFi settings)

# 2. Find the interface
python scripts/find_robot_interface.py --robot-ip 100.96.120.54

# Output: Found interface: wlan0

# 3. Test connection
python scripts/check_g1_connection.py

# 4. Start using with --interface wlan0
python scripts/music/record_music.py --instrument piano --interface wlan0
```

### Switching from Ethernet to WiFi

```bash
# Previously (Ethernet):
python scripts/record.py --interface eth0

# Now (WiFi):
python scripts/record.py --interface wlan0

# That's it! Just change the interface name.
```

### Multiple Networks

If you have both ethernet and WiFi:

```bash
# Check which one can reach robot
python scripts/find_robot_interface.py --robot-ip 100.96.120.54

# Or manually test each
ping -I eth0 100.96.120.54    # Ethernet
ping -I wlan0 100.96.120.54   # WiFi

# Use whichever succeeds
```

## Performance Considerations

### WiFi is Fine For:
- ✅ Recording episodes (50 Hz is easily achievable)
- ✅ Playback of music (not real-time critical)
- ✅ Calibration
- ✅ Configuration

### WiFi May Struggle With:
- ⚠️ Very high frequency control (>200 Hz)
- ⚠️ Hard real-time requirements
- ⚠️ Large data transfers

For music recording/playback at 50 Hz, **WiFi works perfectly fine**!

## Advanced: Static IP Configuration

If you want consistent connection, set a static IP:

**Ubuntu/Debian (netplan):**

```yaml
# /etc/netplan/01-wifi.yaml
network:
  wifis:
    wlan0:
      dhcp4: no
      addresses: [100.96.120.10/24]
      gateway4: 100.96.120.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
      access-points:
        "YourRobotWiFi":
          password: "your-password"
```

Apply:
```bash
sudo netplan apply
```

## Summary

1. **Find your WiFi interface:** `python scripts/find_robot_interface.py`
2. **Use `--interface wlan0`** (or whatever interface was found)
3. **Everything else works the same!**

The system is **fully compatible** with WiFi connections - you just need to specify the correct interface name! 🤖📡

