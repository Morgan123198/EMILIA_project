#!/bin/bash

# Start CBT Bot Script
# This script starts both the CBT bot server and the client using Poetry

echo "Starting CBT Bot..."

# Check if the OPENROUTER_API_KEY is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Error: OPENROUTER_API_KEY environment variable is not set."
    echo "Please set it by running: export OPENROUTER_API_KEY=your_key_here"
    exit 1
fi

# Kill any existing LangGraph server processes
pkill -f "langgraph dev" || echo "No running LangGraph servers found."

# Start the server in the background
echo "Starting LangGraph server..."
poetry run python run_cbt_server.py --port 2024 &
SERVER_PID=$!

# Wait for the server to start
echo "Waiting for server to start (5 seconds)..."
sleep 5

# Check if the server is still running
if ! ps -p $SERVER_PID > /dev/null; then
    echo "Error: Server failed to start."
    exit 1
fi

echo "Server started successfully."
echo "Starting CBT client..."

# Start the client
poetry run python cbt_client.py --server http://localhost:2024 --graph cbt_bot

# When the client exits, kill the server
echo "Client closed. Stopping server..."
kill $SERVER_PID

echo "CBT Bot stopped." 