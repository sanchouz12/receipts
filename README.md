## Setup instruction

1. Install [UV (0.7.19)](https://github.com/astral-sh/uv/releases/tag/0.7.19)
2. Install dependencies
   ```bash
   uv sync --dev
   ```
3. Run the development server
   ```bash
    uv run fastapi dev ./src/main.py
    ```
4. To run tests
   ```bash
   uv run pytest tests/
   ```

## Project structure
```
src/
├── config.py          # Configuration settings
├── db.py              # Database connection
├── main.py            # FastAPI application
├── models/            # SQLAlchemy models
├── routes/            # API endpoints
├── schemas/           # Pydantic schemas
├── dependencies/      # FastAPI dependencies
└── utils/             # Utility functions

tests/
├── conftest.py        # Test configuration
├── test_auth.py       # Authentication tests
└── test_receipts.py   # Receipt functionality tests
```