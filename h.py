import paramiko
import wmi
import winrm
import platform
import subprocess
import socket
import json
from datetime import datetime
import requests


class H:
    def __init__(self):
        self.r = []

    def win(self, i, u, p):
        try:
            s = winrm.Session(f"http://{i}:5985/wsman", auth=(u, p))
            r = s.run_ps("Get-ComputerInfo")
            sys = r.std_out
            d = s.run_ps(
                "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace | ConvertTo-Json"
            )
            disk = json.loads(d.std_out)
            m = s.run_ps(
                "Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json"
            )
            mem = json.loads(m.std_out)
            cpu = s.run_ps(
                "Get-WmiObject -class win32_processor -ErrorAction SilentlyContinue | Measure-Object -property LoadPercentage -Average | Select Average | ConvertTo-Json"
            )
            proc = json.loads(cpu.std_out)
            data = {
                "ip": i,
                "os": "Windows",
                "timestamp": datetime.now().isoformat(),
                "disk": [],
                "memory": {},
                "cpu": {},
                "status": "ok",
            }
            if isinstance(disk, list):
                for dsk in disk:
                    if dsk.get("Size") and dsk.get("FreeSpace"):
                        total = int(dsk["Size"])
                        free = int(dsk["FreeSpace"])
                        data["disk"].append(
                            {
                                "drive": dsk.get("DeviceID", "Unknown"),
                                "total": total,
                                "free": free,
                                "percent_used": ((total - free) / total) * 100,
                            }
                        )
                        if ((total - free) / total) * 100 > 90:
                            data["status"] = "critical"
                        elif ((total - free) / total) * 100 > 80:
                            data["status"] = "warning"
            if isinstance(mem, dict) and mem.get("TotalVisibleMemorySize"):
                total = int(mem["TotalVisibleMemorySize"])
                free = int(mem.get("FreePhysicalMemory", 0))
                data["memory"] = {
                    "total": total,
                    "free": free,
                    "percent_used": ((total - free) / total) * 100,
                }
                if ((total - free) / total) * 100 > 90:
                    data["status"] = "critical"
                elif ((total - free) / total) * 100 > 80:
                    data["status"] = "warning"
            if isinstance(proc, dict) and proc.get("Average"):
                data["cpu"] = {"usage": proc["Average"]}
                if proc["Average"] > 90:
                    data["status"] = "critical"
                elif proc["Average"] > 80:
                    data["status"] = "warning"
            return data
        except Exception as e:
            return {"ip": i, "os": "Windows", "status": "error", "error": str(e)}

    def lin(self, i, u, p, k=None):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if k:
                ssh.connect(i, username=u, key_filename=k, timeout=10)
            else:
                ssh.connect(i, username=u, password=p, timeout=10)
            data = {
                "ip": i,
                "os": "Linux",
                "timestamp": datetime.now().isoformat(),
                "disk": [],
                "memory": {},
                "cpu": {},
                "status": "ok",
            }
            s, o, e = ssh.exec_command("df -h /")
            if o:
                for line in o.read().decode().split("\n"):
                    if line.startswith("/"):
                        p = line.split()
                        if len(p) >= 5:
                            total_str = p[1]
                            used_str = p[2]
                            avail_str = p[3]
                            use_str = p[4].replace("%", "")
                            if "G" in total_str:
                                total = float(total_str.replace("G", "")) * 1024
                            elif "M" in total_str:
                                total = float(total_str.replace("M", ""))
                            else:
                                total = float(total_str.replace("K", "")) / 1024
                            if "G" in used_str:
                                used = float(used_str.replace("G", "")) * 1024
                            elif "M" in used_str:
                                used = float(used_str.replace("M", ""))
                            else:
                                used = float(used_str.replace("K", "")) / 1024
                            percent_used = float(use_str)
                            data["disk"].append(
                                {
                                    "drive": "/",
                                    "total": total,
                                    "used": used,
                                    "free": total - used,
                                    "percent_used": percent_used,
                                }
                            )
                            if percent_used > 90:
                                data["status"] = "critical"
                            elif percent_used > 80:
                                data["status"] = "warning"
            s, o, e = ssh.exec_command("free -m | grep Mem:")
            if o:
                line = o.read().decode().strip()
                if line:
                    p = line.split()
                    total = int(p[1])
                    used = int(p[2])
                    free = (
                        int(p[p.index("available")]) if "available" in p else int(p[3])
                    )
                    data["memory"] = {
                        "total": total,
                        "used": used,
                        "free": free,
                        "percent_used": (used / total) * 100,
                    }
                    if (used / total) * 100 > 90:
                        data["status"] = "critical"
                    elif (used / total) * 100 > 80:
                        data["status"] = "warning"
            s, o, e = ssh.exec_command("uptime")
            if o:
                line = o.read().decode().strip()
                if "load average:" in line:
                    load_part = line.split("load average:")[1].strip()
                    loads = [float(x.strip()) for x in load_part.split(",")]
                    data["cpu"] = {
                        "load_1min": loads[0],
                        "load_5min": loads[1],
                        "load_15min": loads[2],
                    }
                    if loads[0] > 2.0:
                        data["status"] = "critical"
                    elif loads[0] > 1.5:
                        data["status"] = "warning"
            ssh.close()
            return data
        except Exception as e:
            return {"ip": i, "os": "Linux", "status": "error", "error": str(e)}

    def local(self):
        data = {
            "ip": socket.gethostbyname(socket.gethostname()),
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "timestamp": datetime.now().isoformat(),
            "disk": [],
            "memory": {},
            "cpu": {},
            "status": "ok",
        }
        try:
            if platform.system().lower() == "windows":
                c = wmi.WMI()
                for disk in c.Win32_LogicalDisk(DriveType=3):
                    total = int(disk.Size)
                    free = int(disk.FreeSpace)
                    data["disk"].append(
                        {
                            "drive": disk.DeviceID,
                            "total": total,
                            "free": free,
                            "percent_used": ((total - free) / total) * 100,
                        }
                    )
                    if ((total - free) / total) * 100 > 90:
                        data["status"] = "critical"
                    elif ((total - free) / total) * 100 > 80:
                        data["status"] = "warning"
                for mem in c.Win32_OperatingSystem():
                    total = int(mem.TotalVisibleMemorySize)
                    free = int(mem.FreePhysicalMemory)
                    data["memory"] = {
                        "total": total,
                        "free": free,
                        "percent_used": ((total - free) / total) * 100,
                    }
                    if ((total - free) / total) * 100 > 90:
                        data["status"] = "critical"
                    elif ((total - free) / total) * 100 > 80:
                        data["status"] = "warning"
                for proc in c.Win32_Processor():
                    data["cpu"] = {"usage": proc.LoadPercentage}
                    if proc.LoadPercentage > 90:
                        data["status"] = "critical"
                    elif proc.LoadPercentage > 80:
                        data["status"] = "warning"
            else:
                s = subprocess.run(["df", "-h"], capture_output=True, text=True)
                for line in s.stdout.split("\n"):
                    if line.startswith("/dev/"):
                        p = line.split()
                        if len(p) >= 5:
                            total_str = p[1]
                            used_str = p[2]
                            use_str = p[4].replace("%", "")
                            total = float(total_str.replace("G", "")) * 1024
                            used = float(used_str.replace("G", "")) * 1024
                            percent_used = float(use_str)
                            data["disk"].append(
                                {
                                    "drive": p[0],
                                    "total": total,
                                    "used": used,
                                    "free": total - used,
                                    "percent_used": percent_used,
                                }
                            )
                            if percent_used > 90:
                                data["status"] = "critical"
                            elif percent_used > 80:
                                data["status"] = "warning"
                s = subprocess.run(["free", "-m"], capture_output=True, text=True)
                for line in s.stdout.split("\n"):
                    if line.startswith("Mem:"):
                        p = line.split()
                        total = int(p[1])
                        used = int(p[2])
                        free = int(p[p.index("available")] if "available" in p else 3)
                        data["memory"] = {
                            "total": total,
                            "used": used,
                            "free": free,
                            "percent_used": (used / total) * 100,
                        }
                        if (used / total) * 100 > 90:
                            data["status"] = "critical"
                        elif (used / total) * 100 > 80:
                            data["status"] = "warning"
                s = subprocess.run(["uptime"], capture_output=True, text=True)
                if "load average:" in s.stdout:
                    load_part = s.stdout.split("load average:")[1].strip()
                    loads = [float(x.strip()) for x in load_part.split(",")]
                    data["cpu"] = {
                        "load_1min": loads[0],
                        "load_5min": loads[1],
                        "load_15min": loads[2],
                    }
                    if loads[0] > 2.0:
                        data["status"] = "critical"
                    elif loads[0] > 1.5:
                        data["status"] = "warning"
        except Exception as e:
            data["status"] = "error"
            data["error"] = str(e)
        return data


def test():
    h = H()
    print("checking local device...")
    r = h.local()
    print(json.dumps(r, indent=2))
    print("\ntest done!")


if __name__ == "__main__":
    test()
