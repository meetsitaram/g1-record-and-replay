# G1 Connection Check Script

## Quick Start

Simply run:
```bash
cd ~/projects/g1-piano/g1-record-and-replay
source .venv/bin/activate
python scripts/check_g1_connection.py
```

## What It Does

The script performs a comprehensive 3-step check:

### Step 1: Network Interfaces ✅
- Detects all active network interfaces
- Shows IP addresses for each interface
- Filters out loopback and inactive interfaces

Example output:
```
Step 1: Network Interfaces
============================================================
✅ Found 2 active interface(s):

   eth0: 192.168.123.100
   wlan0: 192.168.1.50
```

### Step 2: Robot Reachability ✅
- Pings common G1 IP addresses
- Tests IPs on your local subnets
- Identifies which IP the robot is using

Common G1 IPs tested:
- `192.168.123.161` (default)
- `192.168.123.1` (alternative)
- `192.168.1.161` (alternative subnet)
- Your subnet + `.161`

Example output:
```
Step 2: Robot Reachability
============================================================
Checking common G1 IP addresses...

  Testing 192.168.123.161... ✅ Reachable!
  Testing 192.168.123.1... ❌ Not reachable
  Testing 192.168.1.161... ❌ Not reachable

✅ Robot reachable at: 192.168.123.161
```

### Step 3: SDK Connection Test ✅
- Tries to initialize the SDK on each interface
- Attempts to receive robot state
- Shows sample joint data if successful

Example output:
```
Step 3: SDK Connection Test
============================================================
Testing SDK connection on each interface...

📡 Interface: eth0 (192.168.123.100)
  Attempting SDK connection via eth0...
  Waiting for robot state...
  ✅ Received robot state!
     Sample joint positions: [0.123, -0.456, 0.789, ...]

🎉 SUCCESS! G1 is connected via interface: eth0

You can now use:
  python scripts/calibrate.py --network-interface eth0
  python scripts/record.py --network-interface eth0
  python scripts/replay.py --network-interface eth0 --episode <file>
```

## Success Scenarios

### Scenario 1: Direct Ethernet Connection
```
✅ Found interfaces: eth0
✅ Robot reachable at: 192.168.123.161
✅ SDK connection successful via eth0
```

**Next steps:**
```bash
python scripts/calibrate.py --network-interface eth0
```

### Scenario 2: WiFi Connection
```
✅ Found interfaces: wlan0
✅ Robot reachable at: 192.168.1.161
✅ SDK connection successful via wlan0
```

**Next steps:**
```bash
python scripts/calibrate.py --network-interface wlan0
```

### Scenario 3: Multiple Interfaces
```
✅ Found interfaces: eth0, wlan0
✅ Robot reachable at: 192.168.123.161
✅ SDK connection successful via eth0
```

**Best practice:** Use the interface that succeeded (eth0 in this case)

## Failure Scenarios

### Failure 1: No Robot Found
```
❌ No active network interfaces found!
```

**Fix:**
- Check physical cable connection
- Ensure network adapter is enabled
- Run: `ip a` to see all interfaces

### Failure 2: Robot Not Reachable
```
✅ Found interfaces: eth0
❌ No G1 robot found on common IP addresses
```

**Fix:**
1. Check if robot is powered on
2. Check Ethernet cable is connected to robot
3. Verify robot IP in Unitree app
4. Try manual ping: `ping 192.168.123.161`
5. Check network settings on robot

### Failure 3: Ping Works but SDK Fails
```
✅ Found interfaces: eth0
✅ Robot reachable at: 192.168.123.161
❌ Could not establish SDK connection on any interface
```

**Possible causes:**
- Robot DDS service not running
- Firewall blocking ports 7400-7500
- Wrong network configuration

**Fix:**
```bash
# Check if firewall is blocking
sudo ufw status

# Temporarily disable firewall (for testing)
sudo ufw disable

# Try again
python scripts/check_g1_connection.py

# Re-enable firewall
sudo ufw enable
```

## Troubleshooting Tips

### Tip 1: Find Robot IP Manually
```bash
# Scan your subnet
nmap -sn 192.168.123.0/24

# Or check ARP table
arp -a | grep unitree
```

### Tip 2: Check Physical Connection
```bash
# Check link status
ethtool eth0 | grep "Link detected"

# Should show: Link detected: yes
```

### Tip 3: Verify Robot Is On
- LED indicators should be lit
- Fans should be audible
- Unitree app should show "Connected"

### Tip 4: Check Your Network Settings
```bash
# Show network configuration
ip addr show eth0

# Should have IP in same subnet as robot
# e.g., if robot is 192.168.123.161
# you should be 192.168.123.xxx
```

### Tip 5: Test Without the Script
```bash
# Direct ping test
ping 192.168.123.161

# Manual SDK test
python tests/test_connection.py --network-interface eth0
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| No network interfaces found | Check cable, enable network adapter |
| Robot not reachable | Power on robot, check cable, verify IP |
| SDK timeout | Check firewall, verify DDS ports, try different interface |
| Multiple interfaces | Use the one that succeeded in SDK test |
| Wrong subnet | Configure static IP on your machine |

## For VPN Connections

If connecting via VPN (for later setup), this script will:
- Detect VPN interfaces (tun0, wg0, etc.)
- Test robot reachability through VPN
- Verify SDK connection over VPN

See `VPN_CONNECTION_GUIDE.md` for VPN-specific setup.

## Exit Codes

- `0`: Success - Robot connected
- `1`: Failure - Robot not connected or script error

Use in scripts:
```bash
if python scripts/check_g1_connection.py; then
    echo "Robot connected, proceeding..."
    python scripts/calibrate.py --network-interface eth0
else
    echo "Robot not connected, aborting"
    exit 1
fi
```

## What to Do After Success

Once the script reports success:

```bash
# 1. Calibrate (safe, read-only)
python scripts/calibrate.py --network-interface <interface> --joint-group arms

# 2. Record a test motion
python scripts/record.py --network-interface <interface> --name "test"

# 3. Replay it
python scripts/replay.py --network-interface <interface> --episode data/episodes/<file>.h5
```

Replace `<interface>` with what the script recommended (e.g., `eth0`)

---

**Pro Tip:** Run this script before each session to verify connectivity! 🚀

