import socket
import subprocess
import platform
import threading
import time
import json
import sys
import os
from datetime import datetime

found_stuff = []
thread_lock_thingy = threading.Lock()
settings_stuff = {}


def load_config():
    global settings_stuff
    try:
        with open("config.json", "r") as f:
            settings_stuff = json.load(f)
    except:
        print("No config found, using defaults")
        settings_stuff = {
            "network_range": "192.168.1.1/24",
            "timeout": 2,
            "threads": 50,
            "discord_webhook": "",
            "slack_webhook": "",
            "scan_interval": 300,
        }


def ping_host(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", "-w", str(settings_stuff["timeout"] * 1000), ip]

    try:
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        if b"TTL=" in output or b"bytes from" in output.lower():
            return True
    except:
        pass
    return False


def get_device_info(ip):
    stuff = {
        "ip": ip,
        "hostname": None,
        "mac": None,
        "open_ports": [],
        "status": "unknown",
    }

    try:
        hostname = socket.gethostbyaddr(ip)[0]
        stuff["hostname"] = hostname
    except:
        pass

    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(["arp", "-a", ip], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if ip in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "-" in part and len(part) == 17:
                            stuff["mac"] = part
                            break
    except:
        pass

    ports_to_check = [22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 3389, 5432, 3306]
    stuff["open_ports"] = []

    for port in ports_to_check[:5]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            stuff["open_ports"].append(port)
        sock.close()

    return stuff


def scan_ip(ip):
    global found_stuff

    if ping_host(ip):
        device_details = get_device_info(ip)
        device_details["status"] = "online"
        device_details["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with thread_lock_thingy:
            found_stuff.append(device_details)
            print(f"[+] Found device: {ip} - {device_details['hostname'] or 'Unknown'}")


def scan_network():
    global found_stuff
    found_stuff = []

    network = settings_stuff["network_range"]
    if "/" in network:
        base_ip = network.split("/")[0].rsplit(".", 1)[0]
        last_octet = network.split("/")[0].rsplit(".", 1)[1]
        if "-" in last_octet:
            start, end = map(int, last_octet.split("-"))
        else:
            start, end = 1, 254
    else:
        scan_ip(network)
        return

    print(f"[*] Starting network scan: {network}")
    print(f"[*] Using {settings_stuff['threads']} threads")

    threads = []
    for i in range(start, end + 1):
        ip = f"{base_ip}.{i}"
        t = threading.Thread(target=scan_ip, args=(ip,))
        threads.append(t)
        t.start()

        if len(threads) >= settings_stuff["threads"]:
            for thread in threads:
                thread.join()
            threads = []

    for thread in threads:
        thread.join()

    print(f"[*] Scan complete! Found {len(found_stuff)} devices")


def save_results():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"network_inventory_{timestamp}.json"

    try:
        with open(filename, "w") as f:
            json.dump(found_stuff, f, indent=2)
        print(f"[+] Results saved to {filename}")
        return filename
    except Exception as e:
        print(f"[!] Error saving results: {e}")
        return None


def send_alert(msg):
    if settings_stuff.get("discord_webhook"):
        try:
            import requests

            data = {"content": msg}
            requests.post(settings_stuff["discord_webhook"], json=data, timeout=10)
            print("[+] Discord alert sent")
        except:
            print("[!] Failed to send Discord alert")

    if settings_stuff.get("slack_webhook"):
        try:
            import requests

            data = {"text": msg}
            requests.post(settings_stuff["slack_webhook"], json=data, timeout=10)
            print("[+] Slack alert sent")
        except:
            print("[!] Failed to send Slack alert")


def main():
    print("=" * 50)
    print("    NETWORK INVENTORY SCANNER v1.0")
    print("=" * 50)

    load_config()

    while True:
        try:
            scan_network()

            if found_stuff:
                filename = save_results()

                online_count = len([d for d in found_stuff if d["status"] == "online"])
                print(f"\n[*] Network Summary: {online_count} devices online")

                if online_count < 5:
                    alert_msg = f"🚨 Network Alert: Only {online_count} devices are online! This might indicate a problem."
                    send_alert(alert_msg)

            print(
                f"\n[*] Waiting {settings_stuff['scan_interval']} seconds before next scan..."
            )
            time.sleep(settings_stuff["scan_interval"])

        except KeyboardInterrupt:
            print("\n[*] Scanner stopped by user")
            break
        except Exception as e:
            print(f"[!] Error in main loop: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
