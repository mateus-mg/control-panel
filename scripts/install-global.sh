#!/usr/bin/env bash
# install-global.sh - Install control-panel globally
# Follows the same pattern as other systems (music-automation, media-converter)

set -e

echo "🎛️  Installing Control Panel globally..."
echo "========================================"

# Configuration
SCRIPT_NAME="control_panel.sh"
WRAPPER_NAME="control-panel"
INSTALL_DIR="$HOME/.local/bin"
SCRIPTS_DIR="$HOME/scripts"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running from correct directory
if [ ! -f "$PROJECT_DIR/$SCRIPT_NAME" ]; then
    echo "❌ ERROR: This script must be run from the control-panel directory"
    echo "💡 Navigate to: /media/mateus/Servidor/scripts/control-panel"
    exit 1
fi

# Create installation directory
echo "📁 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Create scripts directory
echo "📁 Creating scripts directory: $SCRIPTS_DIR"
mkdir -p "$SCRIPTS_DIR"

# Check if wrapper already exists
if [ -f "$PROJECT_DIR/$WRAPPER_NAME" ]; then
    echo "ℹ️  Wrapper already exists, updating..."
else
    echo "📝 Creating wrapper script: $WRAPPER_NAME"
fi

# Create wrapper script with auto-sync from HD
cat > "$PROJECT_DIR/$WRAPPER_NAME" << 'WRAPPEREOF'
#!/usr/bin/env bash
# control-panel wrapper - Auto-syncs scripts from HD when mounted

PROJECT_DIR="/media/mateus/Servidor/scripts/control-panel"
HOME_SCRIPTS_DIR="$HOME/scripts"

# Auto-sync function - copies scripts from HD to ~/scripts/
auto_sync() {
    if [ -d "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/scripts/cli_manager.py" ]; then
        if [ -f "$PROJECT_DIR/scripts/log_config.py" ]; then
            cp -p "$PROJECT_DIR/scripts/cli_manager.py" "$HOME_SCRIPTS_DIR/" 2>/dev/null
            cp -p "$PROJECT_DIR/scripts/log_config.py" "$HOME_SCRIPTS_DIR/" 2>/dev/null
            cp -p "$PROJECT_DIR/scripts/log_formatter.py" "$HOME_SCRIPTS_DIR/" 2>/dev/null
            cp -p "$PROJECT_DIR/scripts/backup_cli.py" "$HOME_SCRIPTS_DIR/" 2>/dev/null
            cp -p "$PROJECT_DIR/scripts/backup_config.py" "$HOME_SCRIPTS_DIR/" 2>/dev/null
            cp -p "$PROJECT_DIR/scripts/backup_daemon.py" "$HOME_SCRIPTS_DIR/" 2>/dev/null
            cp -p "$PROJECT_DIR/scripts/backup_manager.py" "$HOME_SCRIPTS_DIR/" 2>/dev/null
            # Also sync docker-compose.yml
            if [ -f "/media/mateus/Servidor/scripts/docker-compose.yml" ]; then
                cp -p "/media/mateus/Servidor/scripts/docker-compose.yml" "$HOME/" 2>/dev/null
            fi
            return 0
        fi
    fi
    return 1
}

# Create ~/scripts if it doesn't exist
mkdir -p "$HOME_SCRIPTS_DIR" 2>/dev/null

# Auto-sync from HD if mounted
auto_sync

# Check if home scripts exist after sync attempt
if [ ! -f "$HOME_SCRIPTS_DIR/cli_manager.py" ]; then
    echo "✗ ERROR: Cannot find control-panel scripts in ~/scripts/"
    echo ""
    echo "💡 SOLUTIONS:"
    echo "   1. Run: control-panel sync"
    echo "   2. Or manually copy:"
    echo "      mkdir -p ~/scripts"
    echo "      cp /media/mateus/Servidor/scripts/control-panel/scripts/*.py ~/scripts/"
    exit 1
fi

# Try to use project venv if HD is mounted
if [ -d "$PROJECT_DIR/venv" ] && [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    exec python3 scripts/cli_manager.py "$@"
fi

# Fallback: use system Python with home scripts
exec python3 "$HOME_SCRIPTS_DIR/cli_manager.py" "$@"
WRAPPEREOF

# Make wrapper executable
chmod +x "$PROJECT_DIR/$WRAPPER_NAME"
echo "✅ Wrapper created: $PROJECT_DIR/$WRAPPER_NAME"

# Create symlink in ~/.local/bin
echo ""
echo "🔗 Creating symlink..."
ln -sf "$PROJECT_DIR/$WRAPPER_NAME" "$INSTALL_DIR/$WRAPPER_NAME" 2>/dev/null || {
    echo "⚠️  Could not create symlink for $WRAPPER_NAME"
}

# Copy main script to ~/scripts/ as backup
echo ""
echo "📋 Copying main script to ~/scripts/ as backup..."
if [ -f "$PROJECT_DIR/$SCRIPT_NAME" ]; then
    cp -p "$PROJECT_DIR/$SCRIPT_NAME" "$SCRIPTS_DIR/$SCRIPT_NAME"
    chmod +x "$SCRIPTS_DIR/$SCRIPT_NAME"
    echo "✅ Script copied to: $SCRIPTS_DIR/$SCRIPT_NAME"
else
    echo "⚠️  Could not find $SCRIPT_NAME in $PROJECT_DIR"
fi

# Check if ~/.local/bin is in PATH
echo ""
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "⚠️  WARNING: $INSTALL_DIR is not in your PATH"
    echo ""
    echo "📋 To fix this, add this line to your ~/.bashrc:"
    echo '   export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    echo "💡 Run these commands:"
    echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "   source ~/.bashrc"
    echo ""
else
    echo "✅ $INSTALL_DIR is in your PATH"
fi

# Check current PATH
echo ""
echo "📋 Your current PATH includes:"
echo "$PATH" | tr ':' '\n' | grep -E "(local|bin)" | head -10

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Available commands:"
echo "   control-panel [command]"
echo "   control-panel [command]  (main command)"
echo ""
echo "🔧 First-time setup:"
echo "   control-panel sync              # Synchronize files"
echo "   control-panel status            # Check system status"
echo ""
echo "🚀 Test installation:"
echo "   control-panel --help            # Show help"
echo "   control-panel version           # Show version (if available)"
echo ""
echo "📁 Files installed:"
echo "   $HOME/.local/bin/control-panel"
echo "   $HOME/control_panel.sh"
echo ""