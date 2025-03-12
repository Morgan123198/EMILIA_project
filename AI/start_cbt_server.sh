#!/bin/bash
# Script to start the LangGraph server for CBT bot

# Check if OpenRouter API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Error: OPENROUTER_API_KEY is not set"
    echo "Please set it with: export OPENROUTER_API_KEY=your_key"
    exit 1
fi

echo "Starting LangGraph server on port 2024..."

# Kill any existing LangGraph process
pkill -f "langgraph up" || true

# First, start langgraph with our config file
poetry run langgraph up --port 2024 -c langgraph.json &

# Store the server PID
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Stopping LangGraph server..."
    kill $SERVER_PID 2>/dev/null || true
    exit 0
}

# Set up trap to cleanup on exit
trap cleanup INT TERM EXIT

echo "LangGraph server running with PID $SERVER_PID"
echo "Press Ctrl+C to stop the server"

# Wait for the server to stop
wait $SERVER_PID 