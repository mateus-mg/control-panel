#!/usr/bin/env bash
# install-service.sh - Install systemd keepalive service
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$PROJECT_DIR/panel-keepalive.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "🔧 Installing control-panel-keepalive.service..."
echo "================================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script requires sudo privileges"
    echo ""
    echo "📋 Run with:"
    echo "   sudo $0"
    exit 1
fi

# 1. Clean old residues
echo "🧹 Cleaning old residues..."
systemctl stop control-panel-keepalive.service 2>/dev/null || true
systemctl disable control-panel-keepalive.service 2>/dev/null || true
rm -f "$SYSTEMD_DIR/control-panel-keepalive.service"

# 2. Copy new unit file
echo "📋 Copying unit file..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/control-panel-keepalive.service"
chmod 644 "$SYSTEMD_DIR/control-panel-keepalive.service"

# 3. Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# 4. Enable and start
echo "🚀 Enabling and starting service..."
systemctl enable control-panel-keepalive.service
systemctl start control-panel-keepalive.service

# 5. Show status
echo ""
echo "✅ Installation complete!"
echo ""
systemctl status control-panel-keepalive.service --no-pager
echo ""
echo "📋 Useful commands:"
echo "   sudo systemctl status control-panel-keepalive.service"
echo "   sudo journalctl -u control-panel-keepalive.service -f"
echo "   sudo systemctl stop control-panel-keepalive.service"
