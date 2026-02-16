# Automated Network Inventory Scanner

**Modern IT Support is moving away from manual work and toward Automation.**

This project automatically scans your network, identifies all connected devices, checks their health, and sends automated alerts when something goes wrong. Perfect for IT Support & SysAdmin who want to look like they know what they're doing! 😎

## What This Does

- **Network Discovery**: Scans your network and finds all connected devices
- **Health Monitoring**: Checks uptime, disk space, memory usage on devices
- **Smart Alerts**: Sends notifications to Discord/Slack when problems happen
- **Auto-Reporting**: Saves scan results and generates reports
- **New Device Detection**: Notifies you when unknown devices join the network

## Installation (Super Easy)

### Prerequisites
- Python 3.7+ (download from python.org if you don't have it)
- Windows/Linux/Mac (works on all of them)
- Admin rights on your network (helps with scanning)

### Setup Steps

1. **Download/Clone this project to a folder**
   ```bash
   git clone https://github.com/yourusername/network-inventory.git
   cd network-inventory
   ```

2. **Install Python packages** (run the batch file, it does this for you)
   ```bash
   pip install requests paramiko wmi pywinrm
   ```

3. **Configure the settings**
   - Open `config.json` in any text editor
   - Change `network_range` to match your network (like "192.168.1.1-254")
   - Add your Discord webhook URL if you want alerts
   - Set up Slack webhook if you prefer Slack
   - Configure email settings if you want email alerts

4. **Run it!**
   - Double-click `run_scanner.bat` on Windows
   - Or run `python network_scanner.py` from command line

## Configuration Guide

### Discord Setup (Recommended)
1. Go to your Discord server settings → Webhooks
2. Create new webhook
3. Copy the URL and paste it in `config.json` where it says "YOUR_DISCORD_WEBHOOK_HERE"

### Slack Setup
1. Go to your Slack workspace → Apps → Build → Custom Integrations → Incoming Webhooks
2. Create webhook and copy URL
3. Paste in `config.json` where it says "YOUR_SLACK_WEBHOOK"

### Network Range
- For single network: `"network_range": "192.168.1.1-254"`
- For specific IPs: `"network_range": "192.168.1.10,192.168.1.20,192.168.1.30"`
- For multiple subnets: Use comma-separated ranges

## Usage

### Quick Start (Windows)
Just double-click `run_scanner.bat` and choose what you want to do:

1. **Quick network scan** - One-time scan, great for testing
2. **Continuous monitoring** - Scans every 5 minutes, perfect for 24/7 monitoring  
3. **Health check only** - Just checks device health, no network scanning
4. **Test alerts** - Sends test notifications to make sure everything works
5. **View results** - Look at previous scan results

### Command Line Usage
```bash
# Quick scan
python network_scanner.py

# Health check only (requires credentials)
python health_checker.py

# Test alerts
python alert_system.py

# Auto modes with batch file
run_scanner.bat scan      # Quick scan
run_scanner.bat monitor   # Continuous monitoring
run_scanner.bat health    # Health check
```

## Advanced Features

### Health Monitoring with Credentials
For detailed health checks on Windows/Linux devices, add credentials to `config.json`:

```json
"device_credentials": {
  "windows_admin_user": "administrator",
  "windows_admin_password": "your_password",
  "linux_ssh_user": "admin", 
  "linux_ssh_password": "your_ssh_password"
}
```

**Security Note**: Use SSH keys instead of passwords when possible!

### Email Alerts
Configure SMTP settings in `config.json`:
```json
"email_settings": {
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "email_user": "your_email@gmail.com",
  "email_password": "your_app_password",
  "email_recipient": "admin@company.com"
}
```

### Custom Alert Levels
Configure what you want to be alerted about:
- New devices joining network
- Devices going offline
- Low disk space (<10% free)
- High memory usage (>90%)
- Critical services stopped

## Output Files

- `network_inventory_YYYYMMDD_HHMMSS.json` - Detailed scan results
- `logs/network_scanner.log` - Application logs
- `config.json` - Your configuration (edit this!)

## Troubleshooting

### "Python not found" Error
- Install Python from python.org
- Make sure to check "Add Python to PATH" during installation

### "Access Denied" Issues
- Run as Administrator on Windows
- Check firewall settings
- Make sure you're on the same network as devices you're scanning

### "Webhook not working"
- Double-check your Discord/Slack webhook URLs
- Make sure internet connection is working
- Try the "Test alerts" option first

### "Can't connect to device"
- Device might be offline
- Check if device is blocking pings
- Verify you have correct credentials for health checks

## What It Looks Like

### Discord Alert Example:
```
🔴 CRITICAL HEALTH ALERT
Device: 192.168.1.100
Issue: Low disk space on C:: 8.5% free

Immediate attention required!
```

### Slack Alert Example:
```
⚠️ New Device Detected
Device: New-Laptop-01  
IP Address: 192.168.1.254
MAC: AA:BB:CC:DD:EE:FF

A new device has joined the network. Please verify if this is authorized.
```

## Pro Tips

1. **Start with Quick Scan** first to make sure everything works
2. **Test Alerts** before setting up continuous monitoring
3. **Check Network Range** - wrong range means no devices found
4. **Monitor the Logs** if something isn't working right
5. **Use SSH Keys** instead of passwords for Linux devices
6. **Set Up Filters** to exclude devices you don't care about

## Security Considerations

- This tool sends network data to Discord/Slack - make sure you're allowed to do that
- Store credentials securely - consider using environment variables for production
- Monitor access to the log files - they contain network information
- Consider running on a dedicated server/network segment

## Cool Things Recruiters Love About This

✅ **Automation**: Replaces manual network inventory tasks  
✅ **Real-time Monitoring**: Catches problems before users complain  
✅ **Multi-platform**: Works on Windows, Linux, Mac  
✅ **Modern Alerts**: Uses Discord/Slack instead of old-school email  
✅ **DevOps Skills**: Shows you understand infrastructure automation  
✅ **Problem Prevention**: Instead of firefighting, you're preventing issues  

## Need Help?

If you run into issues:
1. Check the logs in `logs/network_scanner.log`
2. Make sure your network range is correct
3. Test with a small range first (like just your computer's IP)
4. Join the Discord community (link coming soon)

---

**Made by a sleep-deprived IT guy who was tired of doing manual inventories.**

*If this saves you even 1 hour of work, it was worth creating. Now go impress your manager!* 🚀