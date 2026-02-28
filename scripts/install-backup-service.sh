#!/usr/bin/env bash
# install-backup-service.sh - Install systemd backup daemon service
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$PROJECT_DIR/backup-daemon.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "🔧 Installing control-panel-backup-daemon.service..."
echo "===================================================="

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
systemctl stop control-panel-backup-daemon.service 2>/dev/null || true
systemctl disable control-panel-backup-daemon.service 2>/dev/null || true
rm -f "$SYSTEMD_DIR/control-panel-backup-daemon.service"

# 2. Copy new unit file
echo "📋 Copying unit file..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/control-panel-backup-daemon.service"
chmod 644 "$SYSTEMD_DIR/control-panel-backup-daemon.service"

# 3. Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# 4. Enable and start (enable = start on boot)
echo "🚀 Enabling service (auto-start on boot)..."
systemctl enable control-panel-backup-daemon.service

echo "🚀 Starting service..."
systemctl start control-panel-backup-daemon.service

# 5. Verify enablement
echo ""
echo "🔍 Verifying boot configuration..."
if systemctl is-enabled control-panel-backup-daemon.service &>/dev/null; then
    echo "✅ Service enabled for boot: YES"
else
    echo "❌ Service enabled for boot: NO"
fi

# 5. Show status
echo ""
echo "✅ Installation complete!"
echo ""
systemctl status control-panel-backup-daemon.service --no-pager
echo ""
echo "📋 Useful commands:"
echo "   sudo systemctl status control-panel-backup-daemon.service"
echo "   sudo journalctl -u control-panel-backup-daemon.service -f"
echo "   sudo systemctl stop control-panel-backup-daemon.service"
echo ""
echo "🔄 Service will start automatically on boot"
echo ""
echo "💡 Backup management commands:"
echo "   control-panel backup           # Interactive backup menu"
echo "   control-panel backup-stats     # View statistics"
echo "   control-panel backup-history   # View backup history"
