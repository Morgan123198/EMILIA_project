#!/usr/bin/env python3
"""
Run CBT LangGraph Server

This script initializes and runs the LangGraph server with our CBT bot.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import subprocess
from langgraph.graph import StateGraph
import langgraph

from src.core.cbt_graph import create_cbt_graph
from src.core.config import get_settings
from src.core.llm import llm


def main():
    """Main function to start the LangGraph server with our CBT bot."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the CBT bot LangGraph server.")
    parser.add_argument(
        "--port", type=int, default=2024, help="Port to run the server on"
    )
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Get settings
    settings = get_settings()

    # Validate API key
    if not settings.OPENROUTER_API_KEY:
        print(
            "Error: OPENROUTER_API_KEY is not set in environment variables or .env file"
        )
        print("Please set it and try again")
        sys.exit(1)

    try:
        # Print version information
        print(f"Using LangGraph version: {langgraph.__version__}")
        print(f"Available modules: {dir(langgraph)}")

        # Create the CBT graph
        print(f"Initializing CBT graph with model: {settings.LLM_MODEL}")
        cbt_graph = create_cbt_graph(llm)

        # Start the server using the CLI command
        # This is a more reliable way since the API might change between versions
        print(f"Starting LangGraph server on port {args.port}...")

        cmd = [
            "poetry",
            "run",
            "langgraph",
            "up",
            "--port",
            str(args.port),
            "-c",
            "langgraph.json",
        ]

        # Execute the command
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
