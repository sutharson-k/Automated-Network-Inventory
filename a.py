import requests
import json
import time
from datetime import datetime
from enum import Enum


class L(Enum):
    I = "🔵"
    W = "🟡"
    C = "🔴"
    R = "🟢"


class A:
    def __init__(self, c):
        self.c = c
        self.last = {}
        self.cd = 300

    def d(self, m, l=L.I, t="Network Alert"):
        if not self.c.get("discord_webhook"):
            print("[!] no discord webhook")
            return False
        try:
            col = {L.I: 3447003, L.W: 15844367, L.C: 15158332, L.R: 3066993}
            e = {
                "title": f"{l.value} {t}",
                "description": m,
                "color": col.get(l, 3447003),
                "timestamp": datetime.now().isoformat(),
                "footer": {"text": "Network Scanner"},
            }
            d = {
                "username": "Network Monitor",
                "avatar_url": "https://i.imgur.com/rHsOnjv.png",
                "embeds": [e],
            }
            r = requests.post(self.c["discord_webhook"], json=d, timeout=15)
            if r.status_code == 204:
                print("[+] discord sent")
                return True
            else:
                print(f"[!] discord failed: {r.status_code}")
                return False
        except Exception as e:
            print(f"[!] discord error: {e}")
            return False

    def s(self, m, l=L.I, t="Network Alert"):
        if not self.c.get("slack_webhook"):
            print("[!] no slack webhook")
            return False
        try:
            col = {L.I: "#36a64f", L.W: "#ff9500", L.C: "#ff0000", L.R: "#00ff00"}
            a = {
                "color": col.get(l, "#36a64f"),
                "title": t,
                "text": m,
                "footer": "Network Scanner",
                "ts": int(time.time()),
            }
            d = {
                "username": "Network Monitor",
                "icon_emoji": ":satellite:",
                "attachments": [a],
            }
            r = requests.post(self.c["slack_webhook"], json=d, timeout=15)
            if r.status_code == 200:
                print("[+] slack sent")
                return True
            else:
                print(f"[!] slack failed: {r.status_code}")
                return False
        except Exception as e:
            print(f"[!] slack error: {e}")
            return False

    def e(self, m, l=L.I, t="Network Alert"):
        if not all(
            k in self.c
            for k in [
                "smtp_server",
                "smtp_port",
                "email_user",
                "email_password",
                "email_recipient",
            ]
        ):
            print("[!] email not configured")
            return False
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.c["email_user"]
            msg["To"] = self.c["email_recipient"]
            msg["Subject"] = f"{l.value} {t}"
            body = f"""
Network Alert
============

Level: {l.value} {l.name}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Message:
{m}

---
Sent by Network Scanner
            """
            msg.attach(MIMEText(body, "plain"))
            srv = smtplib.SMTP(self.c["smtp_server"], self.c["smtp_port"])
            srv.starttls()
            srv.login(self.c["email_user"], self.c["email_password"])
            srv.send_message(msg)
            srv.quit()
            print("[+] email sent")
            return True
        except Exception as e:
            print(f"[!] email error: {e}")
            return False

    def send(self, m, l=L.I, t="Network Alert", ch=None):
        if ch is None:
            ch = ["discord", "slack", "email"]
        k = f"{t}:{hash(m)}"
        now = time.time()
        if k in self.last:
            if now - self.last[k] < self.cd:
                print("[!] cooldown active")
                return True
        cnt = 0
        total = 0
        for channel in ch:
            total += 1
            if channel == "discord":
                if self.d(m, l, t):
                    cnt += 1
            elif channel == "slack":
                if self.s(m, l, t):
                    cnt += 1
            elif channel == "email":
                if self.e(m, l, t):
                    cnt += 1
        if cnt > 0:
            self.last[k] = now
            print(f"[*] sent to {cnt}/{total} channels")
            return True
        else:
            print(f"[!] failed to send")
            return False

    def off(self, d):
        m = f"""
**Device Offline**
📱 Device: {d.get("hostname", d.get("ip", "Unknown"))}
🌐 IP: {d.get("ip", "Unknown")}
📍 Last Seen: {d.get("last_seen", "Unknown")}
💻 MAC: {d.get("mac", "Unknown")}

Device was online but is now unreachable.
        """
        return self.send(m, L.C, "Device Offline")

    def on(self, d):
        m = f"""
**Device Back Online** ✅
📱 Device: {d.get("hostname", d.get("ip", "Unknown"))}
🌐 IP: {d.get("ip", "Unknown")}
💻 MAC: {d.get("mac", "Unknown")}
🔌 Ports: {", ".join(map(str, d.get("open_ports", [])))}

Good news! Device is back online.
        """
        return self.send(m, L.R, "Device Recovered")

    def h(self, data):
        if data.get("status") == "critical":
            m = f"""
**🚨 Critical Health**
🖥️ Device: {data.get("ip", "Unknown")}
⚠️ Issue: {data.get("alert", "Unknown health problem")}
📊 Details:
- OS: {data.get("os", "Unknown")}
- Timestamp: {data.get("timestamp", "Unknown")}

Attention required!
            """
            return self.send(m, L.C, "Critical Health")
        elif data.get("status") == "warning":
            m = f"""
**⚠️ Health Warning**
🖥️ Device: {data.get("ip", "Unknown")}
🔍 Issue: {data.get("alert", "Warning detected")}
📊 Details:
- OS: {data.get("os", "Unknown")}
- Timestamp: {data.get("timestamp", "Unknown")}

Monitor closely.
            """
            return self.send(m, L.W, "Health Warning")
        return True

    def sum(self, total, on, off):
        if off > total * 0.2:
            m = f"""
**🚨 Network Alert**
📊 Stats:
- Total: {total}
- Online: {on} ✅
- Offline: {off} ❌
- Health: {(on / total) * 100:.1f}%

>20% devices offline. Network issues?
            """
            return self.send(m, L.C, "Network Health")
        elif off > 0:
            m = f"""
**📈 Network Update**
📊 Stats:
- Total: {total}
- Online: {on} ✅
- Offline: {off} ❌
- Health: {(on / total) * 100:.1f}%

{off} device(s) offline.
            """
            return self.send(m, L.I, "Network Status")
        return True

    def new(self, d):
        m = f"""
**🆕 New Device**
📱 Device: {d.get("hostname", "Unknown")}
🌐 IP: {d.get("ip", "Unknown")}
💻 MAC: {d.get("mac", "Unknown")}
🔌 Ports: {", ".join(map(str, d.get("open_ports", [])))}
📅 First Seen: {d.get("last_seen", "Unknown")}

New device joined network. Verify if authorized.
        """
        return self.send(m, L.W, "New Device")


def test():
    c = {
        "discord_webhook": "YOUR_DISCORD_WEBHOOK_HERE",
        "slack_webhook": "YOUR_SLACK_WEBHOOK_HERE",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_user": "your_email@gmail.com",
        "email_password": "your_app_password",
        "email_recipient": "admin@company.com",
    }
    a = A(c)
    print("testing alerts...")
    a.send("test alert from network scanner", L.I, "Test")
    print("done!")


if __name__ == "__main__":
    test()
