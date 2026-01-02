#!/usr/bin/env python3
"""
Simple script to verify G1 robot connection.
Checks network interfaces, robot reachability, and SDK connectivity.

Usage:
    python scripts/check_g1_connection.py
    python scripts/check_g1_connection.py --robot-ip 100.96.120.54
"""

import subprocess
import re
import sys
import time
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def get_network_interfaces():
    """Get all active network interfaces with IP addresses"""
    try:
        output = subprocess.check_output(['ip', 'addr', 'show'], text=True)
        interfaces = []
        
        current_interface = None
        for line in output.split('\n'):
            # Match interface line
            match = re.match(r'^\d+:\s+(\S+):', line)
            if match:
                interface = match.group(1)
                if interface != 'lo' and 'UP' in line:  # Skip loopback and DOWN interfaces
                    current_interface = interface
            
            # Match IP address for current interface
            if current_interface:
                ip_match = re.search(r'inet (\S+)', line)
                if ip_match:
                    ip = ip_match.group(1).split('/')[0]
                    interfaces.append((current_interface, ip))
                    current_interface = None
        
        return interfaces
    except Exception as e:
        print(f"❌ Error getting interfaces: {e}")
        return []

def check_robot_ping(ip_address, timeout=2):
    """Check if robot IP is reachable via ping"""
    try:
        result = subprocess.run(
            ['ping', '-c', '3', '-W', str(timeout), ip_address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 3
        )
        return result.returncode == 0
    except Exception:
        return False

def try_sdk_connection(interface):
    """Try to connect to robot using SDK"""
    try:
        from g1_record_replay.core import G1Interface
        
        print(f"  Attempting SDK connection via {interface}...")
        interface_obj = G1Interface(interface, use_motion_switcher=False)
        
        # Try to initialize
        interface_obj.initialize()
        
        # Try to get state
        print("  Waiting for robot state...")
        timeout = 5
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            state = interface_obj.get_joint_state()
            if state is not None:
                print(f"  ✅ Received robot state!")
                print(f"     Sample joint positions: {state.positions[:5]}")
                interface_obj.shutdown()
                return True
            time.sleep(0.1)
        
        print(f"  ❌ No state received within {timeout}s")
        interface_obj.shutdown()
        return False
        
    except Exception as e:
        print(f"  ❌ SDK connection failed: {e}")
        return False

def main(robot_ip=None):
    print("\n" + "="*60)
    print("  🤖 G1 Robot Connection Checker")
    print("="*60)
    
    # Step 1: Check network interfaces
    print_section("Step 1: Network Interfaces")
    
    interfaces = get_network_interfaces()
    if not interfaces:
        print("❌ No active network interfaces found!")
        print("   Make sure you're connected to a network.")
        return False
    
    print(f"✅ Found {len(interfaces)} active interface(s):\n")
    for iface, ip in interfaces:
        print(f"   {iface}: {ip}")
    
    # Step 2: Check robot reachability
    print_section("Step 2: Robot Reachability")
    
    # Build list of IPs to check
    ips_to_check = []
    
    if robot_ip:
        # User specified a robot IP
        print(f"Using specified robot IP: {robot_ip}\n")
        ips_to_check = [robot_ip]
    else:
        # Check common default IPs
        print("No robot IP specified, checking common defaults...\n")
        common_robot_ips = [
            '192.168.123.161',  # Default G1 IP
            '192.168.123.1',    # Alternative
            '192.168.1.161',    # Alternative subnet
        ]
        
        # Also check IPs on same subnet as our interfaces
        for iface, ip in interfaces:
            parts = ip.split('.')
            if len(parts) == 4:
                # Add .161 on same subnet
                subnet_ip = f"{parts[0]}.{parts[1]}.{parts[2]}.161"
                if subnet_ip not in common_robot_ips:
                    common_robot_ips.append(subnet_ip)
        
        ips_to_check = common_robot_ips
    
    reachable_ips = []
    
    for test_ip in ips_to_check:
        print(f"  Testing {test_ip}...", end=' ', flush=True)
        if check_robot_ping(test_ip):
            print("✅ Reachable!")
            reachable_ips.append(test_ip)
        else:
            print("❌ Not reachable")
    
    if not reachable_ips:
        print("\n❌ No G1 robot found at specified IP(s)")
        print("\nTroubleshooting:")
        print("  1. Is the robot powered on?")
        print("  2. Is the network connection active (WiFi/Ethernet)?")
        print("  3. Check robot IP in the Unitree app or router")
        print("  4. Try manually: ping <robot-ip>")
        if not robot_ip:
            print("\nℹ️  If you know the robot IP, specify it:")
            print("     python scripts/check_g1_connection.py --robot-ip <ip>")
        return False
    
    print(f"\n✅ Robot reachable at: {', '.join(reachable_ips)}")
    
    # Step 3: Try SDK connection
    print_section("Step 3: SDK Connection Test")
    
    print("Testing SDK connection on each interface...\n")
    
    for iface, ip in interfaces:
        print(f"📡 Interface: {iface} ({ip})")
        
        if try_sdk_connection(iface):
            print(f"\n🎉 SUCCESS! G1 is connected via interface: {iface}")
            print(f"\nYou can now use:")
            print(f"  python scripts/calibrate.py --network-interface {iface}")
            print(f"  python scripts/record.py --network-interface {iface}")
            print(f"  python scripts/replay.py --network-interface {iface} --episode <file>")
            return True
        
        print()  # Blank line between attempts
    
    print("❌ Could not establish SDK connection on any interface")
    print("\nThe robot is reachable via ping, but SDK connection failed.")
    print("\nPossible issues:")
    print("  1. Robot DDS service not running")
    print("  2. Firewall blocking DDS ports (7400-7500)")
    print("  3. Wrong network interface")
    print("\nTry manually:")
    print(f"  python tests/test_connection.py --network-interface {interfaces[0][0]}")
    
    return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Check G1 robot connection and identify correct network interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect robot on common IPs
  python scripts/check_g1_connection.py
  
  # Specify robot IP (e.g., for WiFi)
  python scripts/check_g1_connection.py --robot-ip 100.96.120.54
  
  # First find your WiFi interface
  python scripts/find_robot_interface.py
  # Then check connection
  python scripts/check_g1_connection.py --robot-ip <robot-ip>
        """
    )
    
    parser.add_argument(
        '--robot-ip',
        type=str,
        help='Specific robot IP address to check (e.g., 100.96.120.54 for WiFi)'
    )
    
    args = parser.parse_args()
    
    print("\nChecking G1 robot connection...\n")
    
    try:
        success = main(robot_ip=args.robot_ip)
        
        print("\n" + "="*60)
        if success:
            print("  ✅ Connection check PASSED")
        else:
            print("  ❌ Connection check FAILED")
        print("="*60 + "\n")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

