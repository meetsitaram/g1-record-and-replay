#!/usr/bin/env python3
"""Helper script to find VPN network interface"""

import subprocess
import re
import sys

def get_network_interfaces():
    """Get all network interfaces"""
    try:
        output = subprocess.check_output(['ip', 'a'], text=True)
        interfaces = []
        
        for line in output.split('\n'):
            match = re.match(r'^\d+:\s+(\S+):', line)
            if match:
                interface = match.group(1)
                if interface != 'lo':  # Skip loopback
                    interfaces.append((interface, line))
        
        return interfaces
    except Exception as e:
        print(f"Error getting interfaces: {e}")
        return []

def identify_vpn_interfaces(interfaces):
    """Identify likely VPN interfaces"""
    vpn_patterns = ['tun', 'tap', 'wg', 'vpn', 'ppp', 'utun']
    vpn_interfaces = []
    
    for interface, info in interfaces:
        for pattern in vpn_patterns:
            if pattern in interface.lower():
                vpn_interfaces.append(interface)
                break
    
    return vpn_interfaces

def get_interface_info(interface):
    """Get detailed info about an interface"""
    try:
        output = subprocess.check_output(['ip', 'addr', 'show', interface], text=True)
        
        # Extract IP address
        ip_match = re.search(r'inet (\S+)', output)
        ip = ip_match.group(1) if ip_match else 'No IP'
        
        # Check if UP
        is_up = 'UP' in output
        
        return {
            'ip': ip,
            'status': 'UP' if is_up else 'DOWN'
        }
    except Exception as e:
        return {'ip': 'Unknown', 'status': 'Unknown'}

def main():
    print("🔍 Searching for network interfaces...\n")
    
    interfaces = get_network_interfaces()
    if not interfaces:
        print("❌ Could not detect network interfaces")
        sys.exit(1)
    
    vpn_interfaces = identify_vpn_interfaces(interfaces)
    
    if not vpn_interfaces:
        print("⚠️  No VPN interfaces detected")
        print("\nAvailable interfaces:")
        for interface, _ in interfaces:
            info = get_interface_info(interface)
            print(f"  - {interface}: {info['ip']} ({info['status']})")
        print("\nIf you're connected via VPN, use the interface name from above.")
        print("Example: python scripts/calibrate.py --network-interface eth0")
    else:
        print(f"✅ Found {len(vpn_interfaces)} VPN interface(s):\n")
        
        for interface in vpn_interfaces:
            info = get_interface_info(interface)
            status_icon = "🟢" if info['status'] == 'UP' else "🔴"
            print(f"{status_icon} {interface}")
            print(f"   IP: {info['ip']}")
            print(f"   Status: {info['status']}")
            print()
        
        # Suggest which one to use
        active_vpn = [i for i in vpn_interfaces if get_interface_info(i)['status'] == 'UP']
        
        if active_vpn:
            suggested = active_vpn[0]
            print(f"💡 Suggested interface: {suggested}\n")
            print("To connect to the robot, use:")
            print(f"  python tests/test_connection.py --network-interface {suggested}")
            print(f"  python scripts/calibrate.py --network-interface {suggested}")
            print(f"  python scripts/record.py --network-interface {suggested}")
            print(f"  python scripts/replay.py --network-interface {suggested} --episode <file>")
        else:
            print("⚠️  VPN interfaces found but none are UP")
            print("Please connect your VPN first, then run this script again.")

if __name__ == '__main__':
    main()

