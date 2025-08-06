# GPT Assistant (AIAssistant) Module Documentation

## Overview
This module integrates OpenAI GPT-4o (or other GPT models) into the QGIS plugin as a chatbot assistant. It provides a user interface for asking questions and receiving answers from the OpenAI API.

## Key Files
- `GptAssistantModule.py`: Main entry point, handles UI, API key loading, and error handling.
- `logic/Gpt4oClient.py`: Handles communication with the OpenAI API (using the latest openai>=1.0.0 interface).
- `.env`: Stores the OpenAI API key for development (never commit to public repos).
- `ui/GptAssistantDialog.py`: The PyQt dialog for user interaction.

## API Key Management
- The module loads the API key from `.env` (OPENAI_API_KEY) if not provided directly.
- Supports both `python-dotenv` and manual parsing.

## OpenAI API Usage
- Uses the new OpenAI Python API (>=1.0.0):
  - `openai.OpenAI(api_key=...)` to create a client
  - `client.chat.completions.create(model="gpt-4o", messages=[...])` for chat
- Handles both simple responses and token usage reporting.

## Error Handling
- If the `openai` package is missing, shows a dialog with install instructions.
- If the API key is missing or invalid, the assistant will not function.

## UI/UX
- The assistant dialog is integrated into the plugin sidebar.
- The install manual is shown modelessly, so users can follow instructions while QGIS is open.

## Development Notes
- Always use the latest OpenAI Python package for best compatibility.
- Update `Gpt4oClient.py` if OpenAI changes their API again.
- For production, consider allowing users to enter their own API key securely.

## References
- OpenAI Python API: https://github.com/openai/openai-python
- Migration guide: https://github.com/openai/openai-python/discussions/742
- QGIS Python plugin docs: https://docs.qgis.org/

---
_Last updated: 2025-08-05_
