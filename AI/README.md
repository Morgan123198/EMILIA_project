# CBT Bot

A cognitive behavioral therapy (CBT) assistant built with LangGraph and LangChain.

## Overview

The CBT Bot is an AI-powered assistant that uses cognitive behavioral therapy techniques to help users identify and challenge negative thought patterns. The bot consists of two main components:

1. A listener agent that engages users in conversation and identifies when CBT intervention might be helpful
2. A CBT intervention agent that applies specific therapeutic techniques to help users reframe their thoughts

## Features

- Two-phase conversation model (listening and CBT intervention)
- Automatic detection of cognitive distortions
- Recommendation of appropriate CBT techniques
- Support for conversations in multiple languages
- Saves and loads conversation history
- Powered by Google's Gemini 2.0 through OpenRouter

## Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- OpenRouter API key

## Installation

1. Clone the repository
2. Install dependencies with Poetry:
   ```
   poetry install
   ```
3. Set up your OpenRouter API key:
   ```
   export OPENROUTER_API_KEY=your_key_here
   ```
4. Alternatively, create a `.env` file in the project root with:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```

## Usage

### Starting the CBT Bot

The easiest way to start the bot is using the provided shell script:

```
./start_cbt_bot.sh
```

This will start both the LangGraph server and the interactive client.

### Running Components Separately

To run the server:

```
poetry run python run_cbt_server.py --port 2024
```

To run the interactive client:

```
poetry run python cbt_client.py --server http://localhost:2024 --graph cbt_bot
```

### Testing with JSON Conversations

You can test the bot with pre-defined conversations stored in JSON format:

```
poetry run python cbt_bot_json_test.py --conversation test_conversations/bullying_scenario.json
```

### Using LangGraph CLI Directly

You can also use the LangGraph CLI to start the server:

```
poetry run langgraph dev
```

## Model Configuration

The bot uses Google's Gemini 2.0 through OpenRouter by default, as it provides excellent tool usage capabilities and conversational flow. You can modify the model by changing the `LLM_MODEL` setting in `.env` or the environment variables.

## Project Structure

- `src/agents/` - Contains the listener and CBT intervention agent implementations
- `src/core/` - Core functionality including the CBT graph and routing logic
- `src/prompts/` - Prompt templates for the language models
- `src/schema/` - Type definitions and data structures
- `src/tools/` - Tools for CBT analysis and technique recommendation
- `src/utils/` - Utility functions for state management and conversation parsing

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 