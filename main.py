import time
import socket
import threading
import subprocess
import re
import json
import os
import random
import sys
from datetime import datetime
import concurrent.futures


class S:
    def __init__(self, n, t, p):
        self.n = n
        self.t = t
        self.p = p
        self.a = {}
        self.r = []

    def check(self, h):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.t)
            r = s.connect_ex((h, self.p))
            s.close()
            if r == 0:
                try:
                    tn = socket.gethostbyaddr(h)[0]
                except:
                    tn = h
                try:
                    mac = self.get_mac(h)
                except:
                    mac = "00:00:00:00:00:00"
                self.a[h] = {
                    "ip": h,
                    "hostname": tn,
                    "mac": mac,
                    "open_ports": [self.p],
                    "last_seen": datetime.now().isoformat(),
                }
        except Exception:
            pass

    def get_mac(self, h):
        if os.name == "nt":
            cmd = f"arp -a {h}"
        else:
            cmd = f"arp -n {h}"
        o = subprocess.check_output(cmd, shell=True).decode()
        m = re.search(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})", o)
        if m:
            return m.group(0)
        return "00:00:00:00:00:00"


def ping(h, t):
    cmd = ["ping", "-n" if os.name == "nt" else "-c", "1", "-w", str(t * 1000), h]
    try:
        o = subprocess.run(cmd, capture_output=True, text=True, timeout=t)
        return o.returncode == 0
    except:
        return False


def scan_range(r):
    if "-" in r:
        p = r.split(".")
        b = ".".join(p[:-1])
        d = p[-1].split("-")
        if len(d) == 2:
            s, e = int(d[0]), int(d[1])
            for i in range(s, e + 1):
                yield b + "." + str(i)
        else:
            yield r
    else:
        yield r


def scan():
    try:
        with open("c.json", "r") as f:
            c = json.load(f)
    except:
        c = {
            "network_settings": {
                "network_range": "192.168.1.1-254",
                "timeout": 2,
                "threads": 50,
                "scan_interval": 300,
            }
        }
    n = c["network_settings"]["network_range"]
    t = c["network_settings"]["timeout"]
    th = c["network_settings"]["threads"]

    print(f"[*] scanning: {n}")
    print(f"[*] timeout: {t}s")
    print(f"[*] threads: {th}")

    i = list(scan_range(n))

    print(f"[*] found {len(i)} ips")

    l = []
    for ip in i:
        if ping(ip, t):
            l.append(ip)
            print(f"[+] alive: {ip}")
        else:
            print(f"[-] dead: {ip}")

    print(f"[*] {len(l)} hosts up")

    for ip in l:
        p = [
            22,
            23,
            53,
            80,
            135,
            139,
            443,
            445,
            993,
            995,
            1723,
            3306,
            3389,
            5432,
            5900,
            8080,
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=th) as x:
            futures = []
            for port in p:
                s = S(ip, t, port)
                f = x.submit(s.check, ip)
                futures.append(f)
            concurrent.futures.wait(futures)

    d = []
    for k, v in s.a.items():
        d.append(v)

    print(f"[*] found {len(d)} devices")

    try:
        with open("devices.json", "w") as f:
            json.dump(d, f, indent=2)
        print("[+] saved to devices.json")
    except:
        print("[!] failed to save")

    print("\n[*] results:")
    for d in d:
        print(f"{d['ip']} ({d.get('hostname', 'unknown')}) - ports: {d['open_ports']}")

    return d


def m():
    try:
        with open("devices.json", "r") as f:
            old = json.load(f)
    except:
        old = []

    print("[*] monitoring (ctrl+c to stop)")
    try:
        while True:
            d = scan()

            for a in d:
                if not any(o.get("ip") == a["ip"] for o in old):
                    print(f"[!] new: {a['ip']}")
                    try:
                        from a import A

                        al = A(c)
                        al.new(a)
                    except:
                        pass

            for o in old:
                if not any(a.get("ip") == o["ip"] for a in d):
                    print(f"[!] offline: {o['ip']}")
                    try:
                        from a import A

                        al = A(c)
                        al.off(o)
                    except:
                        pass

            old = d
            time.sleep(c["network_settings"]["scan_interval"])
    except KeyboardInterrupt:
        print("\n[*] stopped")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            m()
        else:
            scan()
    else:
        scan()
