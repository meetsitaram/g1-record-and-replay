#!/usr/bin/env python3
"""
Helper script to find the network interface that can reach the G1 robot.
Works for both Ethernet and WiFi connections.
"""

import subprocess
import re
import sys
import socket
from typing import Optional, List, Tuple


def get_network_interfaces() -> List[Tuple[str, dict]]:
    """Get all active network interfaces with their details"""
    try:
        output = subprocess.check_output(['ip', '-4', 'addr', 'show'], text=True)
        interfaces = []
        
        current_interface = None
        current_ip = None
        
        for line in output.split('\n'):
            # Match interface line: "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>"
            match = re.match(r'^\d+:\s+(\S+):', line)
            if match:
                if current_interface and current_ip:
                    interfaces.append((current_interface, {
                        'ip': current_ip,
                        'status': 'UP'
                    }))
                current_interface = match.group(1)
                current_ip = None
            
            # Match IP line: "    inet 192.168.1.100/24"
            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)', line)
            if ip_match and current_interface:
                current_ip = ip_match.group(1)
                netmask = int(ip_match.group(2))
                
                # Skip loopback
                if current_interface != 'lo':
                    interfaces.append((current_interface, {
                        'ip': current_ip,
                        'netmask': netmask,
                        'status': 'UP'
                    }))
                current_interface = None
                current_ip = None
        
        return interfaces
    except Exception as e:
        print(f"Error getting interfaces: {e}")
        return []


def can_reach_ip(interface: str, target_ip: str) -> bool:
    """
    Check if a network interface can reach the target IP.
    Uses ping with specific interface binding.
    """
    try:
        # Try ping with interface binding
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', '-I', interface, target_ip],
            capture_output=True,
            timeout=3
        )
        return result.returncode == 0
    except:
        return False


def ip_in_subnet(ip: str, subnet_ip: str, netmask: int) -> bool:
    """Check if an IP is in the same subnet"""
    try:
        def ip_to_int(ip_str):
            parts = ip_str.split('.')
            return (int(parts[0]) << 24) + (int(parts[1]) << 16) + \
                   (int(parts[2]) << 8) + int(parts[3])
        
        target = ip_to_int(ip)
        subnet = ip_to_int(subnet_ip)
        mask = (0xFFFFFFFF << (32 - netmask)) & 0xFFFFFFFF
        
        return (target & mask) == (subnet & mask)
    except:
        return False


def find_interface_for_robot(robot_ip: str = "100.96.120.54") -> Optional[str]:
    """
    Find which network interface can reach the robot.
    
    Args:
        robot_ip: IP address of the robot
        
    Returns:
        Interface name (e.g., 'wlan0', 'eth0') or None
    """
    interfaces = get_network_interfaces()
    
    if not interfaces:
        return None
    
    print(f"🔍 Searching for interface that can reach {robot_ip}...\n")
    
    # Strategy 1: Check same subnet (fast)
    print("Strategy 1: Checking subnet matches...")
    for interface, info in interfaces:
        if 'netmask' in info:
            if ip_in_subnet(robot_ip, info['ip'], info['netmask']):
                print(f"  ✓ {interface} ({info['ip']}/{info['netmask']}) - Same subnet!")
                return interface
            else:
                print(f"  ✗ {interface} ({info['ip']}/{info['netmask']}) - Different subnet")
    
    # Strategy 2: Try ping (slower but more reliable)
    print("\nStrategy 2: Testing connectivity with ping...")
    for interface, info in interfaces:
        print(f"  Testing {interface} ({info['ip']})...", end=' ', flush=True)
        if can_reach_ip(interface, robot_ip):
            print("✓ Can reach robot!")
            return interface
        else:
            print("✗ Cannot reach")
    
    return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Find the network interface to reach G1 robot"
    )
    parser.add_argument(
        '--robot-ip',
        type=str,
        default='100.96.120.54',
        help='Robot IP address (default: 100.96.120.54)'
    )
    parser.add_argument(
        '--list-all',
        action='store_true',
        help='List all network interfaces'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("G1 Robot Network Interface Finder")
    print("=" * 60)
    print()
    
    # List all interfaces if requested
    if args.list_all:
        interfaces = get_network_interfaces()
        print("All available network interfaces:\n")
        for interface, info in interfaces:
            # Determine interface type
            if 'wlan' in interface or 'wl' in interface:
                iface_type = "WiFi"
            elif 'eth' in interface or 'enp' in interface or 'ens' in interface:
                iface_type = "Ethernet"
            else:
                iface_type = "Other"
            
            print(f"  🔌 {interface} ({iface_type})")
            print(f"     IP: {info['ip']}")
            if 'netmask' in info:
                print(f"     Netmask: /{info['netmask']}")
            print()
        print()
    
    # Find the right interface for the robot
    robot_ip = args.robot_ip
    interface = find_interface_for_robot(robot_ip)
    
    print()
    print("=" * 60)
    
    if interface:
        print(f"✅ Found interface: {interface}")
        print()
        print(f"The robot at {robot_ip} is reachable via: {interface}")
        print()
        print("Use this interface in your commands:")
        print(f"  python scripts/record.py --interface {interface}")
        print(f"  python scripts/replay.py --interface {interface} --episode <file>")
        print(f"  python scripts/music/record_music.py --instrument piano --interface {interface}")
        print(f"  python scripts/music/play_music.py --instrument piano --interface {interface} --sequence '...'")
    else:
        print("❌ Could not find an interface that can reach the robot")
        print()
        print("Troubleshooting:")
        print(f"  1. Verify robot is reachable: ping {robot_ip}")
        print("  2. Check you're on the same network/WiFi")
        print("  3. Check firewall settings")
        print("  4. Try: python scripts/find_robot_interface.py --list-all")
        print()
        print("Manual specification:")
        print("  If you know the interface name, you can specify it directly:")
        print("  python scripts/record.py --interface wlan0")
        sys.exit(1)
    
    print("=" * 60)


if __name__ == '__main__':
    main()

