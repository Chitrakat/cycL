# Cycling Workout API

FastAPI backend for the cycling workout generation and management system.

## Features

- RESTful API for workout management
- PostgreSQL database integration
- Redis caching support
- Auto-generated API documentation (Swagger/OpenAPI)

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (optional)

### Installation

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and configuration
```

## Running Locally

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

## Available Endpoints

### Health Check
- **GET** `/health` - Returns application health status

### API v1 (Coming soon)
- Workout generation endpoints
- Workout management endpoints
- Template management endpoints

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black app/

# Lint
ruff check app/
```

## Project Structure

```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Configuration and settings
│   ├── db/           # Database models and connection
│   ├── middleware/   # Custom middleware
│   ├── services/     # Business logic
│   └── main.py       # Application entry point
├── requirements.txt  # Python dependencies
└── .env.example      # Environment variables template
```
