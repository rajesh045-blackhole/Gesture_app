#!/bin/bash
set -e

echo "Uninstalling Gesture Control System..."

# 1. Stop services
echo "Stopping services..."
sudo systemctl stop gestured-detector 2>/dev/null || true
sudo systemctl stop gestured-executor 2>/dev/null || true

# 2. Disable services
echo "Disabling services..."
sudo systemctl disable gestured-detector 2>/dev/null || true
sudo systemctl disable gestured-executor 2>/dev/null || true

# 3. Remove systemd files
echo "Removing systemd services..."
sudo rm -f /etc/systemd/system/gestured-detector.service
sudo rm -f /etc/systemd/system/gestured-executor.service
sudo systemctl daemon-reload

# 4. Remove application
echo "Removing application files..."
sudo rm -rf /opt/gestured

# 5. Remove configuration
echo "Removing configuration..."
sudo rm -rf /etc/gestured

# 6. Remove logs
echo "Removing logs..."
sudo rm -rf /var/log/gestured
sudo rm -rf /var/run/gestured

# 7. Remove user (optional)
read -p "Remove system user 'gestured'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo userdel -r gestured 2>/dev/null || true
fi

echo "✓ Uninstallation complete!"
