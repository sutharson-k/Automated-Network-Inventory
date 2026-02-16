import socket
import subprocess
import platform
import threading
import time
import json
import sys
import os
from datetime import datetime

d = []
l = threading.Lock()
c = {}


def load():
    global c
    try:
        with open("config.json", "r") as f:
            c = json.load(f)
    except:
        print("no config found, using defaults")
        c = {
            "network_range": "192.168.1.1/24",
            "timeout": 2,
            "threads": 50,
            "discord_webhook": "",
            "slack_webhook": "",
            "scan_interval": 300,
        }


def ping(i):
    p = "-n" if platform.system().lower() == "windows" else "-c"
    cmd = ["ping", p, "1", "-w", str(c["timeout"] * 1000), i]
    try:
        o = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        if b"TTL=" in o or b"bytes from" in o.lower():
            return True
    except:
        pass
    return False


def info(i):
    x = {
        "ip": i,
        "hostname": None,
        "mac": None,
        "open_ports": [],
        "status": "unknown",
    }
    try:
        h = socket.gethostbyaddr(i)[0]
        x["hostname"] = h
    except:
        pass
    try:
        if platform.system().lower() == "windows":
            r = subprocess.run(["arp", "-a", i], capture_output=True, text=True)
            for line in r.stdout.split("\n"):
                if i in line:
                    y = line.split()
                    for j, part in enumerate(y):
                        if "-" in part and len(part) == 17:
                            x["mac"] = part
                            break
    except:
        pass
    ports = [22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 3389, 5432, 3306]
    x["open_ports"] = []
    for port in ports[:5]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        r = s.connect_ex((i, port))
        if r == 0:
            x["open_ports"].append(port)
        s.close()
    return x


def scan(i):
    global d
    if ping(i):
        x = info(i)
        x["status"] = "online"
        x["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with l:
            d.append(x)
            print(f"[+] found: {i} - {x['hostname'] or 'unknown'}")


def net():
    global d
    d = []
    n = c["network_range"]
    if "/" in n:
        b = n.split("/")[0].rsplit(".", 1)[0]
        last = n.split("/")[0].rsplit(".", 1)[1]
        if "-" in last:
            start, end = map(int, last.split("-"))
        else:
            start, end = 1, 254
    else:
        scan(n)
        return
    print(f"[*] scanning: {n}")
    print(f"[*] threads: {c['threads']}")
    t = []
    for i in range(start, end + 1):
        ip = f"{b}.{i}"
        th = threading.Thread(target=scan, args=(ip,))
        t.append(th)
        th.start()
        if len(t) >= c["threads"]:
            for thread in t:
                thread.join()
            t = []
    for thread in t:
        thread.join()
    print(f"[*] done! found {len(d)} devices")


def save():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    f = f"network_inventory_{ts}.json"
    try:
        with open(f, "w") as file:
            json.dump(d, file, indent=2)
        print(f"[+] saved: {f}")
        return f
    except Exception as e:
        print(f"[!] save error: {e}")
        return None


def alert(msg):
    if c.get("discord_webhook"):
        try:
            import requests

            data = {"content": msg}
            requests.post(c["discord_webhook"], json=data, timeout=10)
            print("[+] discord sent")
        except:
            print("[!] discord failed")
    if c.get("slack_webhook"):
        try:
            import requests

            data = {"text": msg}
            requests.post(c["slack_webhook"], json=data, timeout=10)
            print("[+] slack sent")
        except:
            print("[!] slack failed")


def main():
    print("=" * 50)
    print("    NETWORK SCANNER v1.0")
    print("=" * 50)
    load()
    while True:
        try:
            net()
            if d:
                f = save()
                on = len([x for x in d if x["status"] == "online"])
                print(f"\n[*] summary: {on} devices online")
                if on < 5:
                    a = f"🚨 alert: only {on} devices online!"
                    alert(a)
            print(f"\n[*] waiting {c['scan_interval']} seconds...")
            time.sleep(c["scan_interval"])
        except KeyboardInterrupt:
            print("\n[*] stopped")
            break
        except Exception as e:
            print(f"[!] error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
