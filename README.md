# Zomato Restaurant Recommendation System

AI-powered restaurant recommendation engine matching user preferences with the Hugging Face Zomato Bangalore dataset.

## Setup Instructions

1. **Python Version**: This project supports Python 3.9+.
2. **Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Modify `.env` to include your `LLM_API_KEY` and other custom preferences.

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Project Layout

- `src/`: Core codebase.
  - `config.py`: Environment configuration loader.
  - `data/`: Ingestion, schema models, and store access logic.
- `tests/`: Automated unit tests.
- `data/cache/`: Downloaded and processed datasets cache directory.

## Testing

To run the automated test suite, execute the following command:
```bash
pytest
```
