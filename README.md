# ListenWifi Monitor

Auto-discovers ListenWifi (Exxothermic) audio servers on your LAN via mDNS,
relays each channel as an HTTP MP3 stream, and provides a live web dashboard.

| Port | What it serves |
|------|----------------|
| 6000 | Web dashboard |
| 6001 | Server 1 (lowest IP) — Channel 1 |
| 6002 | Server 1 — Channel 2 |
| 6003 | Server 2 (2nd lowest IP) — Channel 1 |
| … | … |
| 6012 | Server 6 (highest IP) — Channel 2 |

Stream ports are assigned by ascending server IP then ascending channel number
and recomputed automatically if the server list changes.

---

## Requirements

- Windows 11 (64-bit)
- Administrator access (for service installation)
- Same LAN / VLAN as the ListenWifi servers
- Internet access during installation only

---

## Installation

Open **Windows Terminal** or **PowerShell** as **Administrator** for every step below.

---

### Step 1 — Install Python 3.11

```powershell
winget install Python.Python.3.11
```

Close and reopen your terminal, then confirm:

```powershell
python --version
```

---

### Step 2 — Install ffmpeg

```powershell
winget install Gyan.FFmpeg
```

Close and reopen your terminal, then confirm:

```powershell
ffmpeg -version
```

> If `winget` can't find it, download the full build from https://www.gyan.dev/ffmpeg/builds/
> and add the `bin\` folder to your system PATH.

---

### Step 3 — Get the project

```powershell
cd C:\
git clone <your-repo-url> ListenWifi2Streams
cd C:\ListenWifi2Streams\listenifi_monitor
```

Or download and extract the ZIP, then `cd` into `listenifi_monitor\`.

---

### Step 4 — Create a virtual environment and install Python packages

```powershell
cd C:\ListenWifi2Streams\listenifi_monitor

python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt
```

---

### Step 5 — Install the Opus audio codec (opus.dll)

`opuslib` is a Python wrapper — it needs the native `opus.dll` alongside the script.

**Download a pre-built DLL:**

1. Go to https://github.com/ShiftMediaProject/opus/releases
2. Download the latest `opus_YYYY-MM-DD_msvc17.zip`
3. Inside the ZIP, find `bin\x64\opus.dll`
4. Copy it to `C:\ListenWifi2Streams\listenifi_monitor\`

Confirm Python can find it:

```powershell
.\venv\Scripts\python -c "import opuslib; print('Opus OK')"
```

---

### Step 6 — Open Windows Firewall ports

Run as Administrator:

```powershell
# Dashboard and MP3 stream ports (allow other machines to connect via VLC)
netsh advfirewall firewall add rule `
  name="ListenWifi Monitor - HTTP" `
  dir=in action=allow protocol=TCP localport=6000-6012

# RTP inbound — lets the ListenWifi servers send audio back to this machine
netsh advfirewall firewall add rule `
  name="ListenWifi Monitor - RTP" `
  dir=in action=allow protocol=UDP localport=49152-65535
```

---

### Step 7 — Test manually (recommended before installing the service)

```powershell
cd C:\ListenWifi2Streams\listenifi_monitor
.\venv\Scripts\activate
python app.py
```

Open **http://localhost:6000** — the dashboard should load and begin scanning.
Press `Ctrl+C` to stop when satisfied.

---

### Step 8 — Install NSSM (service manager)

NSSM wraps any executable as a Windows service with automatic restart on failure.

1. Download `nssm-<version>.zip` from **https://nssm.cc/download**
2. Extract and copy `win64\nssm.exe` to `C:\Windows\System32\`
3. Confirm: `nssm --version`

---

### Step 9 — Create the Windows service

Run PowerShell as **Administrator**. Adjust the path if you cloned somewhere else.

```powershell
$appDir = "C:\ListenWifi2Streams\listenifi_monitor"
$python  = "$appDir\venv\Scripts\python.exe"

# Create the service
nssm install ListenWifiMonitor $python app.py

# Working directory (required — app.py imports local modules)
nssm set ListenWifiMonitor AppDirectory   $appDir

# Description shown in services.msc
nssm set ListenWifiMonitor Description    "ListenWifi audio stream monitor and relay"

# Start automatically at boot, without any user logged in
nssm set ListenWifiMonitor Start          SERVICE_AUTO_START

# Log stdout + stderr to a file (rotated at 5 MB)
New-Item -ItemType Directory -Force "$appDir\logs" | Out-Null
nssm set ListenWifiMonitor AppStdout      "$appDir\logs\service.log"
nssm set ListenWifiMonitor AppStderr      "$appDir\logs\service.log"
nssm set ListenWifiMonitor AppRotateFiles  1
nssm set ListenWifiMonitor AppRotateBytes  5242880

# Auto-restart: wait 5 s after a crash, back off if crashing repeatedly
nssm set ListenWifiMonitor AppRestartDelay 5000
nssm set ListenWifiMonitor AppThrottle     30000

# Start it now
nssm start ListenWifiMonitor
```

Confirm it is running:

```powershell
nssm status ListenWifiMonitor   # Expected: SERVICE_RUNNING
```

Open **http://localhost:6000** — the dashboard should be live with no user session required.

---

## Managing the service

All commands require an **Administrator** prompt.

| Action | Command |
|--------|---------|
| Start | `nssm start ListenWifiMonitor` |
| Stop | `nssm stop ListenWifiMonitor` |
| Restart | `nssm restart ListenWifiMonitor` |
| Remove | `nssm remove ListenWifiMonitor confirm` |
| Edit settings (GUI) | `nssm edit ListenWifiMonitor` |
| View logs | `notepad C:\ListenWifi2Streams\listenifi_monitor\logs\service.log` |

The service starts at boot and restarts within 5 seconds after any crash.

---

## Listening to a stream

Once the dashboard shows a channel as **Receiving RTP**:

1. Open VLC → **Media → Open Network Stream**
2. Enter the URL shown on the channel card, e.g. `http://192.168.1.100:6001/`
3. VLC's "Now Playing" displays the channel title automatically

Multiple VLC instances can connect to the same port simultaneously.

---

## Troubleshooting

**Dashboard loads but no servers appear**
- Confirm the ListenWifi units and this PC are on the same subnet / VLAN.
- mDNS (UDP 5353) must not be blocked between them. Try temporarily disabling
  Windows Firewall to test: `netsh advfirewall set allprofiles state off`
  (re-enable after: `netsh advfirewall set allprofiles state on`)

**Channel stays "Requesting…" and never turns green**
- The firewall rule for UDP 49152–65535 inbound (Step 6) may be missing.
- Check the log for errors: `notepad ...\logs\service.log`

**ffmpeg not found error in logs**
- Run `ffmpeg -version` in a *new* terminal. If missing, reinstall via winget.
- The service runs as SYSTEM and may have a different PATH. Hardcode the path
  in `stream_server.py`: change `shutil.which("ffmpeg")` to return the full
  path, e.g. `C:\ProgramData\chocolatey\bin\ffmpeg.exe`.

**`opuslib` ImportError or OSError**
- Confirm `opus.dll` is in `C:\ListenWifi2Streams\listenifi_monitor\`.
- Confirm it is the **x64** build (matches 64-bit Python).

**Service fails to start / exits immediately**
- Check: `notepad C:\ListenWifi2Streams\listenifi_monitor\logs\service.log`
- Ensure the SYSTEM account has Read & Execute on the project folder:
  `icacls C:\ListenWifi2Streams /grant "NT AUTHORITY\SYSTEM:(OI)(CI)RX" /T`

**Port 6000 already in use**
- Find the process: `netstat -ano | findstr :6000`
- Kill it or change `WEB_PORT` in `app.py` and recreate the service.
