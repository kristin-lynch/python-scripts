#!/usr/bin/env python3
"""
Network Scanner - Wraps nmap to discover hosts and open ports on a local network
Author: Kristin Lynch
Date: 2026-05-05
"""

import sys
import socket
import subprocess
import nmap
from datetime import datetime


def get_local_network():
    """Detect the local machine's IP and return the subnet in CIDR notation."""
    try:
        # Connect to an external address to determine the local IP (no data sent)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Assume a /24 subnet (e.g. 192.168.1.0/24)
        subnet = ".".join(local_ip.split(".")[:3]) + ".0/24"
        return local_ip, subnet
    except Exception as e:
        print(f"Could not detect local network: {e}")
        sys.exit(1)


def check_nmap_installed():
    """Verify that nmap is installed and accessible."""
    result = subprocess.run(["which", "nmap"], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ nmap is not installed. Run: brew install nmap")
        sys.exit(1)


def scan_network(target, scan_type="basic"):
    """
    Scan the target network or host.

    scan_type options:
        'ping'  - Host discovery only (fast, no port scan)
        'basic' - Common ports (top 100)
        'full'  - All 65535 ports (slow)
    """
    nm = nmap.PortScanner()

    scan_args = {
        "ping":  "-sn",
        "basic": "-F",           # Fast scan: top 100 ports
        "full":  "-p-",          # All ports
    }.get(scan_type, "-F")

    print(f"\nScanning: {target}")
    print(f"Scan type: {scan_type}  |  Arguments: {scan_args}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        nm.scan(hosts=target, arguments=scan_args)
    except nmap.PortScannerError as e:
        print(f"❌ Scan error: {e}")
        print("   Try running with sudo for more accurate results.")
        sys.exit(1)

    hosts_up = []

    for host in nm.all_hosts():
        status = nm[host].state()
        hostname = nm[host].hostname() or "unknown"

        if status == "up":
            hosts_up.append(host)
            print(f"\n🟢 Host: {host}  ({hostname})  [{status}]")

            # Print open ports if any were scanned
            for proto in nm[host].all_protocols():
                ports = sorted(nm[host][proto].keys())
                for port in ports:
                    port_info = nm[host][proto][port]
                    if port_info["state"] == "open":
                        service = port_info.get("name", "unknown")
                        print(f"   ✅ {proto.upper()} {port:>5}  {service}")

    print(f"\n{'=' * 60}")
    print(f"Summary: {len(hosts_up)} host(s) up out of {len(nm.all_hosts())} scanned")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    return hosts_up


if __name__ == "__main__":
    check_nmap_installed()

    local_ip, subnet = get_local_network()
    print("Network Scanner")
    print("=" * 60)
    print(f"Local IP : {local_ip}")
    print(f"Subnet   : {subnet}")

    # Change scan_type to 'ping' (fastest) or 'full' (thorough)
    scan_network(target=subnet, scan_type="basic")
