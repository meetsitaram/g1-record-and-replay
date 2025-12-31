# Connecting to G1 Robot via VPN

## Overview

When the G1 robot is accessible through a VPN instead of a direct network connection, you need to configure the SDK to communicate over the VPN interface.

## Method 1: Use VPN Interface Name (Recommended)

### Step 1: Find Your VPN Interface

```bash
# Show all network interfaces
ip a

# Example output:
# ...
# 5: tun0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500
#     inet 10.8.0.2/24 ...
```

Common VPN interface names:
- **OpenVPN**: `tun0`, `tun1`, `tap0`
- **WireGuard**: `wg0`, `wg1`
- **Generic VPN**: `vpn0`, `ppp0`

### Step 2: Use the VPN Interface

Simply pass the VPN interface name to the scripts:

```bash
# Test connection (replace tun0 with your VPN interface)
python tests/test_connection.py --network-interface tun0

# Calibrate
python scripts/calibrate.py --network-interface tun0 --joint-group arms

# Record
python scripts/record.py --network-interface tun0 --name "test_motion"

# Replay
python scripts/replay.py --network-interface tun0 --episode data/episodes/episode_001.h5
```

---

## Method 2: Check Network Connectivity First

Before running the scripts, verify you can reach the robot:

```bash
# Find robot IP (check your VPN configuration)
# Common robot IPs:
# - 192.168.123.161 (default G1 IP)
# - 10.x.x.x (VPN assigned)
# - Check your VPN client for the robot's IP

# Ping the robot
ping <robot-ip>

# Check if DDS ports are accessible (optional)
# DDS uses UDP port 7400 by default
nc -u -v <robot-ip> 7400
```

---

## Method 3: Environment Variable for DDS Configuration (If Method 1 Fails)

If using the VPN interface directly doesn't work, you can configure DDS more explicitly:

### Create a cyclonedds config file

```bash
cat > ~/cyclonedds.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
    <Domain id="any">
        <General>
            <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
        </General>
        <Discovery>
            <ParticipantIndex>auto</ParticipantIndex>
            <Peers>
                <Peer address="<ROBOT_IP>"/>
            </Peers>
        </Discovery>
    </Domain>
</CycloneDDS>
EOF
```

Replace `<ROBOT_IP>` with your robot's actual IP address.

### Use the config file

```bash
export CYCLONEDDS_URI=file://$HOME/cyclonedds.xml
python scripts/calibrate.py --network-interface tun0
```

---

## Troubleshooting

### Issue 1: "Failed to receive robot state"

**Possible causes:**
- VPN not connected
- Wrong interface name
- Firewall blocking DDS traffic
- Robot not powered on

**Solutions:**
```bash
# 1. Verify VPN is connected
ip a show tun0  # Replace with your interface

# 2. Check you can ping the robot
ping <robot-ip>

# 3. Try without specifying interface (let DDS auto-detect)
python tests/test_connection.py

# 4. Check DDS traffic isn't blocked
# Temporarily disable firewall (be careful!)
sudo ufw status
```

### Issue 2: "No route to host"

**Solution:**
```bash
# Check routing table
ip route

# Ensure VPN routes to robot subnet
# You might need to add a route:
sudo ip route add <robot-subnet>/24 via <vpn-gateway> dev tun0
```

### Issue 3: High Latency/Lag

VPN connections add latency. This affects:
- **Calibration**: ✅ Should work fine (read-only)
- **Recording**: ✅ Should work (passive mode)
- **Replay**: ⚠️ May be jerky due to latency

**Tips for better replay over VPN:**
- Use slower playback speed: `--speed 0.5`
- Ensure stable VPN connection
- Consider using local recording and replaying on-site

---

## Example: Full Workflow Over VPN

```bash
# 1. Connect to VPN (using your VPN client)
# ...VPN connects, creates tun0...

# 2. Verify connectivity
ping 192.168.123.161  # or your robot's IP

# 3. Activate venv
cd ~/projects/g1-piano/g1-record-and-replay
source .venv/bin/activate

# 4. Test connection
python tests/test_connection.py --network-interface tun0

# 5. If test passes, proceed with operations
python scripts/calibrate.py --network-interface tun0 --joint-group arms
```

---

## VPN-Specific Considerations

### Bandwidth
- **Recording**: ~10-20 KB/s (low bandwidth)
- **Replay**: ~20-50 KB/s (moderate bandwidth)
- **Most VPNs**: Should handle this easily

### Latency
- **Acceptable**: < 50ms
- **Usable**: 50-200ms  
- **Problematic**: > 200ms

Test your latency:
```bash
ping -c 10 <robot-ip>
```

### Firewall/NAT
Some VPNs use strict NAT. If you have issues:
1. Check if UDP traffic is allowed
2. Ensure ports 7400-7500 (DDS range) are open
3. Contact your VPN admin if needed

---

## Quick Reference

| Scenario | Command |
|----------|---------|
| Test VPN connection | `python tests/test_connection.py --network-interface tun0` |
| Calibrate over VPN | `python scripts/calibrate.py --network-interface tun0` |
| Record over VPN | `python scripts/record.py --network-interface tun0 --name "vpn_test"` |
| Replay over VPN | `python scripts/replay.py --network-interface tun0 --episode <file> --speed 0.5` |

**Pro Tip:** Create an alias for convenience:
```bash
echo 'alias g1="python -m g1_record_replay --network-interface tun0"' >> ~/.bashrc
```

---

## When VPN Isn't Working

If you continue having issues:

1. **Use the robot's app** to verify it's online
2. **Check SDK examples** work over VPN:
   ```bash
   cd ~/projects/g1-piano/unitree_sdk2_python/example/g1/low_level
   python g1_low_level_example.py tun0
   ```
3. **Contact support** with:
   - VPN type (OpenVPN, WireGuard, etc.)
   - Robot IP address
   - Output of `ip route`
   - Error messages

---

## Summary

**Best Practice for VPN Connection:**

1. ✅ Use VPN interface name directly (`tun0`, `wg0`, etc.)
2. ✅ Test connection first
3. ✅ Use slower replay speeds
4. ✅ Calibration and recording work great over VPN
5. ⚠️ Replay may have slight lag depending on latency

**Most Common Working Setup:**
```bash
python scripts/calibrate.py --network-interface tun0
```

That's it! The SDK handles the rest automatically. 🚀

