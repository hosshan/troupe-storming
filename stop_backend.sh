#!/bin/bash

echo "Stopping TinyTroupe backend processes..."

# Find and stop Python processes related to the application
echo "Finding Python processes..."
ps aux | grep -E "(uvicorn|python.*app|python.*main)" | grep -v grep

# Stop processes gracefully first
echo "Attempting graceful shutdown..."
pkill -f "uvicorn.*app.main:app"
pkill -f "python.*main.py"
pkill -f "python.*-m uvicorn"

# Wait a moment for graceful shutdown
sleep 3

# Force kill if still running
echo "Force stopping remaining processes..."
pkill -9 -f "uvicorn.*app.main:app" 2>/dev/null
pkill -9 -f "python.*main.py" 2>/dev/null
pkill -9 -f "python.*-m uvicorn" 2>/dev/null

# Check if any processes are still running
echo "Checking for remaining processes..."
REMAINING=$(ps aux | grep -E "(uvicorn|python.*app|python.*main)" | grep -v grep)
if [ -z "$REMAINING" ]; then
    echo "✅ All backend processes stopped successfully"
else
    echo "⚠️  Some processes may still be running:"
    echo "$REMAINING"
fi

echo "Backend shutdown complete" 