#!/usr/bin/env python3
"""
Automated Network Inventory Script

This script discovers network devices, collects information about them,
and stores the data for inventory purposes.
"""

import subprocess
import ipaddress
import socket
import json
import sqlite3
from datetime import datetime
import argparse
import sys


def ping_device(ip):
    """Check if a device is reachable via ping."""
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '2', str(ip)], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False


def get_hostname(ip):
    """Get hostname for an IP address."""
    try:
        return socket.gethostbyaddr(str(ip))[0]
    except socket.herror:
        return str(ip)


def scan_network(network_range):
    """Scan a network range for active devices."""
    network = ipaddress.IPv4Network(network_range, strict=False)
    active_devices = []
    
    print(f"Scanning network {network}...")
    
    for ip in network:
        if ping_device(ip):
            hostname = get_hostname(ip)
            device_info = {
                'ip': str(ip),
                'hostname': hostname,
                'timestamp': datetime.now().isoformat()
            }
            active_devices.append(device_info)
            print(f"Found device: {ip} ({hostname})")
    
    return active_devices


def setup_database():
    """Create SQLite database and table for storing inventory."""
    conn = sqlite3.connect('network_inventory.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            hostname TEXT,
            mac_address TEXT,
            vendor TEXT,
            os_type TEXT,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn


def save_to_database(devices):
    """Save discovered devices to the database."""
    conn = setup_database()
    cursor = conn.cursor()
    
    for device in devices:
        cursor.execute('''
            INSERT OR REPLACE INTO devices (ip_address, hostname, last_seen)
            VALUES (?, ?, ?)
        ''', (device['ip'], device['hostname'], device['timestamp']))
    
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Automated Network Inventory')
    parser.add_argument('network', help='Network range to scan (e.g., 192.168.1.0/24)')
    parser.add_argument('--output', '-o', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    # Validate network range
    try:
        ipaddress.IPv4Network(args.network, strict=False)
    except ValueError:
        print(f"Invalid network range: {args.network}")
        sys.exit(1)
    
    # Scan the network
    active_devices = scan_network(args.network)
    
    # Save to database
    save_to_database(active_devices)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(active_devices, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print("\nDiscovered devices:")
        for device in active_devices:
            print(f"  {device['ip']} ({device['hostname']}) - Last seen: {device['timestamp']}")


if __name__ == "__main__":
    main()