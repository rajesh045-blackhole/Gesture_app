# Gesture Control System - Production Deployment Guide

## Prerequisites

- Python 3.8+
- systemd (Linux)
- macOS 10.15+ (for macOS deployment, requires adaptation of services)
- sudo access for installation

## Installation

### 1. Clone Repository
```bash
git clone <your-repo> /tmp/gestured-install
cd /tmp/gestured-install
```

### 2. Run Installation Script
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

This will:
- Create system user `gestured` (unprivileged)
- Install files to `/opt/gestured`
- Copy configuration to `/etc/gestured`
- Create log directories
- Install and enable systemd services

### 3. Verify Installation
```bash
# Check services are installed
systemctl list-unit-files | grep gestured

# Check service status
sudo systemctl status gestured-detector
sudo systemctl status gestured-executor
```

## Running the System

### Start Services
```bash
sudo systemctl start gestured-detector
sudo systemctl start gestured-executor
```

### Stop Services
```bash
sudo systemctl stop gestured-detector
sudo systemctl stop gestured-executor
```

### View Logs
```bash
# Detector logs (Structured JSON)
sudo journalctl -u gestured-detector -f

# Executor logs (Structured JSON)
sudo journalctl -u gestured-executor -f

# Both services
sudo journalctl -u gestured-* -f
```

### Check Service Health
```bash
sudo systemctl status gestured-detector
sudo systemctl status gestured-executor

# Detailed health check
python3 utils/health_check.py
```

## Configuration

### Edit Gesture Mappings
```bash
sudo nano /etc/gestured/gesture_config.yaml
```

After changes:
```bash
sudo systemctl restart gestured-executor
```

### Adjust Resource Limits
Edit `/etc/systemd/system/gestured-*.service`:
```bash
sudo nano /etc/systemd/system/gestured-executor.service
# Then reload
sudo systemctl daemon-reload
sudo systemctl restart gestured-executor
```

## Troubleshooting

### Services fail to start
```bash
# Check detailed error
sudo systemctl status gestured-detector
journalctl -xe

# Check permissions
ls -la /opt/gestured
ls -la /etc/gestured
id gestured
```

### Camera not detected
```bash
# Check camera permissions
ls -la /dev/video*

# Add gestured user to video group
sudo usermod -aG video gestured

# Restart
sudo systemctl restart gestured-detector
```

### Media control not working
```bash
# Check music app is running
# Verify AppleScript access (macOS):
# System Preferences → Security & Privacy → Accessibility
#  Add Terminal / Python to list
```

## Uninstallation

```bash
chmod +x scripts/uninstall.sh
./scripts/uninstall.sh
```

## Monitoring & Metrics

### Using systemd journal
```bash
# Last 50 lines
sudo journalctl -u gestured-detector -n 50

# Since last hour
sudo journalctl -u gestured-detector --since "1 hour ago"

# Export to JSON for analysis
sudo journalctl -u gestured-detector -o json > logs.json
```

### Performance metrics
```bash
# Memory usage
ps aux | grep gestured

# CPU usage
top -p $(pgrep -f gesture_detector)
```

## Security Best Practices

1. **Keep permissions strict:**
   - Detector: unprivileged user
   - Executor: minimal capabilities needed

2. **Monitor logs:**
   - Review action audit logs regularly
   - Alert on unexpected gesture events

3. **Update regularly:**
   - Keep TensorFlow/MediaPipe updated
