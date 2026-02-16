import paramiko
import wmi
import winrm
import platform
import subprocess
import socket
import json
from datetime import datetime
import requests


class HealthChecker:
    def __init__(self):
        self.results = []

    def check_windows_device(self, ip, username, password):
        try:
            session = winrm.Session(
                f"http://{ip}:5985/wsman", auth=(username, password)
            )

            # Get system info
            result = session.run_ps("Get-ComputerInfo")
            system_info = result.std_out

            # Get disk usage
            disk_result = session.run_ps(
                "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace | ConvertTo-Json"
            )
            disk_info = json.loads(disk_result.std_out)

            # Get services status
            service_result = session.run_ps(
                'Get-Service | Where-Object {$_.Status -eq "Stopped" -and $_.StartType -eq "Automatic"} | Select-Object Name, DisplayName | ConvertTo-Json'
            )
            stopped_services = (
                json.loads(service_result.std_out) if service_result.std_out else []
            )

            health_data = {
                "ip": ip,
                "os": "Windows",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "uptime": self._parse_uptime(system_info),
                "disk_usage": disk_info,
                "stopped_services": stopped_services,
                "status": "healthy",
            }

            # Check for issues
            if disk_info:
                for disk in disk_info if isinstance(disk_info, list) else [disk_info]:
                    free_space_gb = int(disk["FreeSpace"]) / (1024**3)
                    total_space_gb = int(disk["Size"]) / (1024**3)
                    free_percent = (free_space_gb / total_space_gb) * 100

                    if free_percent < 10:  # less than 10% free
                        health_data["status"] = "warning"
                        health_data["alert"] = (
                            f"Low disk space on {disk['DeviceID']}: {free_percent:.1f}% free"
                        )

            if stopped_services and len(stopped_services) > 0:
                health_data["status"] = "critical"
                health_data["alert"] = (
                    f"{len(stopped_services)} critical services stopped"
                )

            return health_data

        except Exception as e:
            return {
                "ip": ip,
                "os": "Windows",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "error",
                "error": f"Connection failed: {str(e)}",
            }

    def check_linux_device(self, ip, username, password=None, ssh_key=None):
        # Check Linux device health using SSH
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if ssh_key:
                ssh.connect(ip, username=username, key_filename=ssh_key, timeout=10)
            else:
                ssh.connect(ip, username=username, password=password, timeout=10)

            health_data = {
                "ip": ip,
                "os": "Linux",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "healthy",
            }

            # Get uptime
            stdin, stdout, stderr = ssh.exec_command("uptime")
            uptime_output = stdout.read().decode().strip()
            health_data["uptime"] = uptime_output

            # Get disk usage
            stdin, stdout, stderr = ssh.exec_command('df -h | grep -E "^/dev/"')
            disk_output = stdout.read().decode().strip()
            health_data["disk_usage"] = disk_output

            # Check for low disk space
            for line in disk_output.split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 5 and parts[4].endswith("%"):
                        usage_percent = int(parts[4].rstrip("%"))
                        if usage_percent > 90:
                            health_data["status"] = "critical"
                            health_data["alert"] = (
                                f"High disk usage on {parts[5]}: {usage_percent}%"
                            )

            # Check load average
            stdin, stdout, stderr = ssh.exec_command("cat /proc/loadavg")
            load_output = stdout.read().decode().strip()
            load_avg = float(load_output.split()[0])
            health_data["load_average"] = load_avg

            if load_avg > 2.0:  # high load
                if health_data["status"] == "healthy":
                    health_data["status"] = "warning"
                health_data["alert"] = f"High system load: {load_avg}"

            # Check memory usage
            stdin, stdout, stderr = ssh.exec_command("free -m | grep Mem")
            mem_output = stdout.read().decode().strip()
            if mem_output:
                mem_parts = mem_output.split()
                if len(mem_parts) >= 3:
                    total_mem = int(mem_parts[1])
                    used_mem = int(mem_parts[2])
                    mem_percent = (used_mem / total_mem) * 100

                    if mem_percent > 90:
                        if health_data["status"] == "healthy":
                            health_data["status"] = "warning"
                        health_data["alert"] = f"High memory usage: {mem_percent:.1f}%"

                    health_data["memory_usage"] = f"{mem_percent:.1f}%"

            ssh.close()
            return health_data

        except Exception as e:
            return {
                "ip": ip,
                "os": "Linux",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "error",
                "error": f"SSH connection failed: {str(e)}",
            }

    def check_local_device(self):
        # Check health of the machine this script is running on
        try:
            health_data = {
                "ip": "localhost",
                "os": platform.system(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "healthy",
            }

            system = platform.system().lower()

            if system == "windows":
                # Windows checks
                try:
                    c = wmi.WMI()

                    # CPU usage
                    cpu_info = c.Win32_Processor()[0]
                    health_data["cpu_usage"] = f"{cpu_info.LoadPercentage}%"

                    # Memory
                    memory = c.Win32_OperatingSystem()[0]
                    total_mem = int(memory.TotalVisibleMemorySize)
                    free_mem = int(memory.FreePhysicalMemory)
                    used_mem = total_mem - free_mem
                    mem_percent = (used_mem / total_mem) * 100

                    health_data["memory_usage"] = f"{mem_percent:.1f}%"
                    if mem_percent > 90:
                        health_data["status"] = "warning"
                        health_data["alert"] = f"High memory usage: {mem_percent:.1f}%"

                    # Disk space
                    disks = c.Win32_LogicalDisk(DriveType=3)
                    disk_info = []
                    for disk in disks:
                        free_space = int(disk.FreeSpace)
                        total_space = int(disk.Size)
                        free_percent = (free_space / total_space) * 100

                        disk_info.append(
                            {
                                "drive": disk.DeviceID,
                                "free_percent": free_percent,
                                "free_gb": free_space / (1024**3),
                            }
                        )

                        if free_percent < 10:
                            health_data["status"] = "warning"
                            health_data["alert"] = (
                                f"Low disk space on {disk.DeviceID}: {free_percent:.1f}% free"
                            )

                    health_data["disks"] = disk_info

                except Exception as e:
                    health_data["error"] = f"WMI access failed: {str(e)}"
                    health_data["status"] = "error"

            else:
                # Linux/Mac checks
                try:
                    # Memory
                    result = subprocess.run(
                        ["free", "-m"], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        lines = result.stdout.split("\n")
                        for line in lines:
                            if line.startswith("Mem:"):
                                parts = line.split()
                                total = int(parts[1])
                                used = int(parts[2])
                                percent = (used / total) * 100
                                health_data["memory_usage"] = f"{percent:.1f}%"

                                if percent > 90:
                                    health_data["status"] = "warning"
                                    health_data["alert"] = (
                                        f"High memory usage: {percent:.1f}%"
                                    )
                                break

                    # Disk usage
                    result = subprocess.run(
                        ["df", "-h"], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        lines = result.stdout.split("\n")
                        for line in lines:
                            if line.startswith("/dev/"):
                                parts = line.split()
                                if len(parts) >= 5:
                                    usage_percent = int(parts[4].rstrip("%"))
                                    if usage_percent > 90:
                                        health_data["status"] = "warning"
                                        health_data["alert"] = (
                                            f"High disk usage: {usage_percent}%"
                                        )

                    # Load average
                    result = subprocess.run(["uptime"], capture_output=True, text=True)
                    if result.returncode == 0:
                        health_data["uptime"] = result.stdout.strip()

                except Exception as e:
                    health_data["error"] = f"System commands failed: {str(e)}"
                    health_data["status"] = "error"

            return health_data

        except Exception as e:
            return {
                "ip": "localhost",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "error",
                "error": f"Health check failed: {str(e)}",
            }

    def _parse_uptime(self, system_info):
        # Parse uptime from PowerShell output
        try:
            lines = system_info.split("\n")
            for line in lines:
                if "UpTime" in line or "LastBootUpTime" in line:
                    return line.strip()
            return "Unknown"
        except:
            return "Unknown"

    def check_device(self, ip, device_type="auto", credentials=None):
        # Main method to check device health
        print(f"[*] Checking health of {ip} ({device_type})")

        if ip == "localhost" or ip == "127.0.0.1":
            return self.check_local_device()

        if device_type == "windows":
            if credentials:
                return self.check_windows_device(
                    ip, credentials["username"], credentials["password"]
                )
            else:
                return {
                    "ip": ip,
                    "status": "error",
                    "error": "No credentials provided for Windows",
                }

        elif device_type == "linux":
            if credentials:
                return self.check_linux_device(
                    ip,
                    credentials["username"],
                    credentials.get("password"),
                    credentials.get("ssh_key"),
                )
            else:
                return {
                    "ip": ip,
                    "status": "error",
                    "error": "No credentials provided for Linux",
                }

        else:
            # Auto-detect - try some basic checks
            # This is very basic, could be improved
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((ip, 22))
                sock.close()

                if result == 0:
                    return {
                        "ip": ip,
                        "status": "info",
                        "message": "SSH port open, likely Linux device",
                    }

                result = socket.connect_ex((ip, 3389))
                if result == 0:
                    return {
                        "ip": ip,
                        "status": "info",
                        "message": "RDP port open, likely Windows device",
                    }

                return {
                    "ip": ip,
                    "status": "info",
                    "message": "Device reachable but type unknown",
                }

            except:
                return {
                    "ip": ip,
                    "status": "error",
                    "error": "Cannot determine device type",
                }
