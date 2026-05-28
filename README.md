# AI-auto-improvement

## Getting Started

### Local Setup

Create a `.env` file in the project root with the following keys:

```
DATABASE_URL=sqlite+aiosqlite:///./app.db
GEMINI_API_KEY=your_gemini_api_key
REVIEW_TRIGGER_LIMIT=20
LLM_MODEL_NAME=gemini-2.0-flash-lite
```

Seed the database with the initial prompt and golden samples:

```
python -m scripts.seed_db
```

Start the FastAPI server:

```
uvicorn src.main:app --reload
```