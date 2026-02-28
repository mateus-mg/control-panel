#!/bin/bash

echo "🧪 Testing control-panel commands..."
echo "====================================="

# Testar se o comando control-panel está disponível
if command -v control-panel &> /dev/null; then
    echo "✅ control-panel command is available"
else
    echo "❌ control-panel command is NOT available"
    echo "💡 Run: ./install-global.sh first"
fi

echo ""
echo "📋 Available commands:"
echo "   control-panel status"
echo "   control-panel sync"
echo "   control-panel mount"
echo "   control-panel unmount"
echo "   control-panel keepalive"
echo "   control-panel start [service]"
echo "   control-panel stop [service]"
echo "   control-panel restart [service]"
echo "   control-panel logs [service]"
echo "   control-panel ps"
echo "   control-panel services"
echo "   control-panel check"
echo "   control-panel fix"
echo "   control-panel view-logs"
echo "   control-panel diagnose"
echo ""
echo "💡 To install globally, run: ./install-global.sh"
echo "💡 To synchronize files, run: control-panel sync"