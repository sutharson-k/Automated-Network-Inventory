#!/usr/bin/env python3
# Alert System for Network Inventory
# Sends alerts to Discord or Slack when stuff breaks
# Author: Overworked IT Admin

import requests
import json
import time
from datetime import datetime
from enum import Enum


class AlertLevel(Enum):
    INFO = "🔵"
    WARNING = "🟡"
    CRITICAL = "🔴"
    RESOLVED = "🟢"


class AlertManager:
    def __init__(self, config):
        self.config = config
        self.last_alerts = {}  # prevent spam
        self.cooldown_time = 300  # 5 minutes between same alert

    def send_discord_alert(self, message, level=AlertLevel.INFO, title="Network Alert"):
        if not self.config.get("discord_webhook"):
            print("[!] Discord webhook not configured")
            return False

        try:
            # Discord embed format
            color_map = {
                AlertLevel.INFO: 3447003,  # blue
                AlertLevel.WARNING: 15844367,  # yellow
                AlertLevel.CRITICAL: 15158332,  # red
                AlertLevel.RESOLVED: 3066993,  # green
            }

            embed = {
                "title": f"{level.value} {title}",
                "description": message,
                "color": color_map.get(level, 3447003),
                "timestamp": datetime.now().isoformat(),
                "footer": {"text": "Network Inventory Scanner"},
            }

            data = {
                "username": "Network Monitor",
                "avatar_url": "https://i.imgur.com/rHsOnjv.png",  # generic server icon
                "embeds": [embed],
            }

            response = requests.post(
                self.config["discord_webhook"], json=data, timeout=15
            )

            if response.status_code == 204:
                print("[+] Discord alert sent successfully")
                return True
            else:
                print(f"[!] Discord alert failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"[!] Error sending Discord alert: {e}")
            return False

    def send_slack_alert(self, message, level=AlertLevel.INFO, title="Network Alert"):
        if not self.config.get("slack_webhook"):
            print("[!] Slack webhook not configured")
            return False

        try:
            # Slack message format
            color_map = {
                AlertLevel.INFO: "#36a64f",
                AlertLevel.WARNING: "#ff9500",
                AlertLevel.CRITICAL: "#ff0000",
                AlertLevel.RESOLVED: "#00ff00",
            }

            attachment = {
                "color": color_map.get(level, "#36a64f"),
                "title": title,
                "text": message,
                "footer": "Network Inventory Scanner",
                "ts": int(time.time()),
            }

            data = {
                "username": "Network Monitor",
                "icon_emoji": ":satellite:",
                "attachments": [attachment],
            }

            response = requests.post(
                self.config["slack_webhook"], json=data, timeout=15
            )

            if response.status_code == 200:
                print("[+] Slack alert sent successfully")
                return True
            else:
                print(f"[!] Slack alert failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"[!] Error sending Slack alert: {e}")
            return False

    def send_email_alert(self, message, level=AlertLevel.INFO, title="Network Alert"):
        # Basic email alert (could be improved)
        if not all(
            k in self.config
            for k in [
                "smtp_server",
                "smtp_port",
                "email_user",
                "email_password",
                "email_recipient",
            ]
        ):
            print("[!] Email not properly configured")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.config["email_user"]
            msg["To"] = self.config["email_recipient"]
            msg["Subject"] = f"{level.value} {title}"

            body = f"""
Network Alert Report
====================

Level: {level.value} {level.name}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Message:
{message}

---
Sent by Network Inventory Scanner
            """

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
            server.starttls()
            server.login(self.config["email_user"], self.config["email_password"])
            server.send_message(msg)
            server.quit()

            print("[+] Email alert sent successfully")
            return True

        except Exception as e:
            print(f"[!] Error sending email alert: {e}")
            return False

    def send_alert(
        self, message, level=AlertLevel.INFO, title="Network Alert", channels=None
    ):
        # Send to all configured channels
        if channels is None:
            channels = ["discord", "slack", "email"]

        success_count = 0
        total_channels = 0

        # Check cooldown to prevent spam
        alert_key = f"{title}:{hash(message)}"
        current_time = time.time()

        if alert_key in self.last_alerts:
            if current_time - self.last_alerts[alert_key] < self.cooldown_time:
                print(f"[*] Alert cooldown active, skipping duplicate alert")
                return True

        for channel in channels:
            total_channels += 1
            if channel == "discord":
                if self.send_discord_alert(message, level, title):
                    success_count += 1
            elif channel == "slack":
                if self.send_slack_alert(message, level, title):
                    success_count += 1
            elif channel == "email":
                if self.send_email_alert(message, level, title):
                    success_count += 1

        if success_count > 0:
            self.last_alerts[alert_key] = current_time
            print(f"[*] Alert sent to {success_count}/{total_channels} channels")
            return True
        else:
            print(f"[!] Failed to send alert to any channel")
            return False

    def device_offline_alert(self, device_info):
        message = f"""
**Device Offline Detected**
📱 Device: {device_info.get("hostname", device_info.get("ip", "Unknown"))}
🌐 IP Address: {device_info.get("ip", "Unknown")}
📍 Last Seen: {device_info.get("last_seen", "Unknown")}
💻 MAC: {device_info.get("mac", "Unknown")}

This device was previously online but is now unreachable.
        """
        return self.send_alert(message, AlertLevel.CRITICAL, "Device Offline")

    def device_online_alert(self, device_info):
        message = f"""
**Device Back Online** ✅
📱 Device: {device_info.get("hostname", device_info.get("ip", "Unknown"))}
🌐 IP Address: {device_info.get("ip", "Unknown")}
💻 MAC: {device_info.get("mac", "Unknown")}
🔌 Open Ports: {", ".join(map(str, device_info.get("open_ports", [])))}

Good news! This device is back online.
        """
        return self.send_alert(message, AlertLevel.RESOLVED, "Device Recovered")

    def health_check_alert(self, health_data):
        if health_data.get("status") == "critical":
            message = f"""
**🚨 CRITICAL HEALTH ISSUE**
🖥️ Device: {health_data.get("ip", "Unknown")}
⚠️ Issue: {health_data.get("alert", "Unknown health problem")}
📊 Details:
- OS: {health_data.get("os", "Unknown")}
- Uptime: {health_data.get("uptime", "Unknown")}
- Timestamp: {health_data.get("timestamp", "Unknown")}

Immediate attention required!
            """
            return self.send_alert(
                message, AlertLevel.CRITICAL, "Critical Health Alert"
            )

        elif health_data.get("status") == "warning":
            message = f"""
**⚠️ Health Warning**
🖥️ Device: {health_data.get("ip", "Unknown")}
🔍 Issue: {health_data.get("alert", "Warning detected")}
📊 Details:
- OS: {health_data.get("os", "Unknown")}
- Timestamp: {health_data.get("timestamp", "Unknown")}

Monitor this device closely.
            """
            return self.send_alert(message, AlertLevel.WARNING, "Health Warning")

        return True

    def network_summary_alert(self, total_devices, online_devices, offline_devices):
        if offline_devices > total_devices * 0.2:  # more than 20% offline
            message = f"""
**🚨 Network Health Alert**
📊 Network Statistics:
- Total Devices: {total_devices}
- Online: {online_devices} ✅
- Offline: {offline_devices} ❌
- Health: {(online_devices / total_devices) * 100:.1f}%

More than 20% of devices are offline. This may indicate network issues.
            """
            return self.send_alert(message, AlertLevel.CRITICAL, "Network Health Alert")

        elif offline_devices > 0:
            message = f"""
**📈 Network Status Update**
📊 Network Statistics:
- Total Devices: {total_devices}
- Online: {online_devices} ✅
- Offline: {offline_devices} ❌
- Health: {(online_devices / total_devices) * 100:.1f}%

{offline_devices} device(s) currently offline.
            """
            return self.send_alert(message, AlertLevel.INFO, "Network Status")

        return True

    def new_device_alert(self, device_info):
        message = f"""
**🆕 New Device Detected**
📱 Device: {device_info.get("hostname", "Unknown")}
🌐 IP Address: {device_info.get("ip", "Unknown")}
💻 MAC: {device_info.get("mac", "Unknown")}
🔌 Open Ports: {", ".join(map(str, device_info.get("open_ports", [])))}
📅 First Seen: {device_info.get("last_seen", "Unknown")}

A new device has joined the network. Please verify if this is authorized.
        """
        return self.send_alert(message, AlertLevel.WARNING, "New Device Alert")


# Test function
def test_alerts():
    # Test configuration
    test_config = {
        "discord_webhook": "YOUR_DISCORD_WEBHOOK_HERE",
        "slack_webhook": "YOUR_SLACK_WEBHOOK_HERE",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_user": "your_email@gmail.com",
        "email_password": "your_app_password",
        "email_recipient": "admin@company.com",
    }

    alert_manager = AlertManager(test_config)

    print("Testing alert system...")
    alert_manager.send_alert(
        "This is a test alert from the network scanner.", AlertLevel.INFO, "Test Alert"
    )
    print("Test complete!")


if __name__ == "__main__":
    test_alerts()
