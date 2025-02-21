# CloudTunnel

## 🚀 About the Project

Note: This project is still in the alpha stage. You may experience bugs, glitches, or unexpected behavior. Please report any issues on GitHub.

**Disclaimer:** This project is an independent initiative and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Cloudflare or Playit.gg.

This script automates the setup of a **Playit.gg tunnel** for exposing a local server to the internet. Additionally, it updates **Cloudflare DNS records** to link a domain with the exposed Playit address. This is useful for services like **Minecraft servers**, game hosting, and other applications requiring external access.

## 📌 Features
- **Automatic Playit Installation & Setup**
- **Automatic Cloudflare DNS Updates**
- **SRV Record Management for Minecraft**
- **Real-time Monitoring of Playit Tunnel**
- **Multi-Architecture Support (x86-64, ARM, etc.)**

## 📋 Prerequisites
Make sure you have:
- A **Cloudflare** account with a domain.
- A **Playit.gg** account.
- Python 3 installed.
- Linux system (Ubuntu/Debian recommended).
- Installed dependencies: `requests` (install via `pip install requests`).

## 🔧 Installation & Setup
### 1️⃣ Clone the Repository
```sh
 git clone https://github.com/Obsivium/CloudTunnel.git
 cd CloudTunnel
```

### 2️⃣ Run the Script
```sh
chmod +x main.py
./main.py
```

### 3️⃣ Provide Credentials
- **Cloudflare Zone ID**: Found in Cloudflare Dashboard.
- **Cloudflare API Token**: Needs DNS edit permissions.
- **SRV Record Selection**: Choose the Minecraft (or other) SRV record.

The script will handle Playit installation, tunnel creation, and Cloudflare DNS updates.

## 🛠 How It Works
1. **Downloads and configures Playit** based on your system architecture.
2. **Checks for existing Cloudflare DNS records** and updates them with the Playit public address.
3. **Monitors Playit** for changes and applies them to Cloudflare automatically.
4. **Provides a stable domain link** for your Playit tunnel.

## 🛑 Troubleshooting
### Playit Not Generating an Address?
- Run Playit manually:
```sh
./playit-linux-amd64
```
- Check logs for an exposed address.

### Cloudflare DNS Not Updating?
- Make sure Cloudflare Proxy (⚡) is **disabled**.
- Flush DNS Cache:
```sh
sudo systemd-resolve --flush-caches
```

### Minecraft Server Shows "Unknown Host"?
- Run:
```sh
nslookup mc.yourdomain.com
```
- If no result, check Cloudflare settings.

## 📜 License
This project is licensed under the **GNU GENERAL PUBLIC LICENSE V3.0**.

## ✉️ Support
For issues or contributions, open a GitHub issue!

**Author:** [Obsivium](https://github.com/Obsivium)

