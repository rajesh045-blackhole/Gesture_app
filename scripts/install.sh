#!/bin/bash
set -e

echo "Installing Gesture Control System..."

# 1. Create system user (unprivileged)
if ! id -u gestured > /dev/null 2>&1; then
    echo "Creating system user 'gestured'..."
    sudo useradd -r -s /usr/sbin/nologin -d /nonexistent -m gestured
else
    echo "User 'gestured' already exists."
fi

# 2. Create directories
echo "Creating directories..."
sudo mkdir -p /opt/gestured
sudo mkdir -p /etc/gestured
sudo mkdir -p /var/log/gestured
sudo mkdir -p /var/run/gestured

# 3. Copy files
echo "Installing application files..."
sudo cp -r . /opt/gestured/
sudo chown -R gestured:gestured /opt/gestured
sudo chmod 755 /opt/gestured

# 4. Copy configuration
echo "Installing configuration..."
sudo cp config/gesture_config.yaml /etc/gestured/gesture_config.yaml
sudo chown root:root /etc/gestured/gesture_config.yaml
sudo chmod 644 /etc/gestured/gesture_config.yaml

# 5. Set permissions
echo "Setting permissions..."
sudo chown root:gestured /var/log/gestured
sudo chmod 775 /var/log/gestured
sudo chown root:gestured /var/run/gestured
sudo chmod 775 /var/run/gestured

# 6. Install systemd services
echo "Installing systemd services..."
sudo cp systemd/gestured-detector.service /etc/systemd/system/
sudo cp systemd/gestured-executor.service /etc/systemd/system/
sudo systemctl daemon-reload

# 7. Enable services
echo "Enabling services..."
sudo systemctl enable gestured-detector.service
sudo systemctl enable gestured-executor.service

echo "✓ Installation complete!"
echo ""
echo "To start the services:"
echo "  sudo systemctl start gestured-detector"
echo "  sudo systemctl start gestured-executor"
echo ""
echo "To check status:"
echo "  sudo systemctl status gestured-detector"
echo "  sudo systemctl status gestured-executor"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u gestured-detector -f"
echo "  sudo journalctl -u gestured-executor -f"
