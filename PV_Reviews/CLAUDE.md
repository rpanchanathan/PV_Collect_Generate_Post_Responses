# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Google Reviews automation system for **Paati Veedu**, a South Indian vegetarian restaurant in Chennai. The system scrapes Google reviews, generates AI-powered responses using Anthropic's Claude API, and posts replies back to Google My Business.

## Refactored Architecture (2025)

### Folder Structure
```
PV_Reviews/
├── src/
│   ├── collectors/          # Review scraping modules
│   ├── processors/          # Response generation
│   ├── posters/            # Response posting
│   └── utils/              # Common utilities
├── config/                 # Configuration management
├── data/                   # CSV files, progress tracking
├── logs/                   # Application logs
├── archive/               # Legacy scripts
└── requirements-clean.txt  # Essential dependencies only
```

### Core Components

#### Review Collection (`src/collectors/review_collector.py`)
- **GoogleAuthenticator**: Handles Google account login
- **ReviewExtractor**: Extracts comprehensive review data
- **ReviewCollector**: Main orchestrator with proper error handling
- Focuses only on unreplied reviews
- Saves to timestamped CSV files in `data/`

#### Configuration (`config/settings.py`) 
- Centralized configuration using dataclasses
- Environment variable management
- Business-specific constants (listing ID, URLs)
- Browser and API settings

#### Utilities (`src/utils/`)
- **logging_config.py**: Structured logging setup
- Consistent error handling patterns

### Legacy Files
Legacy scripts moved to `archive/` folder:
- Old versions: `get_reviews_*.py`, `Generate_Responses_Old.py`
- Alternative implementations: `simplified_*.py`, experimental scripts

## Setup Instructions

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install clean dependencies
pip install -r requirements-clean.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Install Playwright browsers
```bash
playwright install chromium
```

## Common Commands

### Collect Unreplied Reviews
```bash
# New refactored collector
python src/collectors/review_collector.py

# Legacy collector (archived)
python archive/get_reviews.py
```

### Generate Responses
```bash
python src/processors/Generate_Responses.py
```

### Post Responses
```bash
python src/posters/post_Suggested_Responses_Batch.py
```

## Environment Variables Required

Copy `.env.example` to `.env` and configure:
- `GOOGLE_EMAIL` - Google account for My Business access  
- `GOOGLE_PASSWORD` - Google account password
- `ANTHROPIC_API_KEY` - Claude API key for response generation

## Data Flow

1. **Collection**: `review_collector.py` → `data/reviews_unreplied_TIMESTAMP.csv`
2. **Processing**: `Generate_Responses.py` → `data/review_responses_TIMESTAMP.csv` 
3. **Posting**: `post_Suggested_Responses_Batch.py` → Updates Google My Business

## Configuration

All settings centralized in `config/settings.py`:
- Business listing ID: `11382416837896137085`
- Browser settings, timeouts, batch sizes
- File paths and naming conventions
- Claude API parameters

## Security Notes

- `.env` file is gitignored and contains sensitive credentials
- Use `.env.example` as template
- Data files and logs are excluded from version control
- Progress tracking files stored in `data/` directory

## Development Notes

- Clean dependency management with `requirements-clean.txt`
- Structured logging to `logs/` directory
- Type hints and error handling throughout
- Modular design for easier testing and maintenance