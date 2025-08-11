# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the backend API for Squeeze, an educational LMS focused on text analysis and visualization for startup club reflection papers. The system analyzes Korean text using NLP techniques and provides insights through word frequency analysis, word grouping, and theme summarization.

## Technology Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL via Supabase
- **Caching**: Redis (cloud-hosted)
- **NLP**: Okt (Korean morphological analyzer)
- **Authentication**: JWT-based
- **File Storage**: Supabase Storage

## Key Commands

### Development Setup
```bash
# Install dependencies (once requirements.txt is created)
pip install -r requirements.txt

# Run the development server
uvicorn main:app --reload --port 8000

# Run with specific environment
uvicorn main:app --reload --port 8000 --env-file .env.local
```

### Testing
```bash
# Run all tests (once pytest is set up)
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Code Quality
```bash
# Format code with black (once installed)
black .

# Check linting with ruff (once installed)
ruff check .

# Type checking with mypy (once installed)
mypy .
```

## Architecture Overview

### API Structure
The API should be organized following FastAPI best practices:
- `app/` - Main application directory
  - `api/` - API routes organized by feature
  - `core/` - Core functionality (config, security, dependencies)
  - `models/` - Pydantic models for request/response
  - `services/` - Business logic and external service integrations
  - `db/` - Database models and migrations
  - `utils/` - Utility functions

### Key Endpoints (from specs/api-spec.md)
1. **Text Analysis Pipeline**:
   - `/upload-text` - Upload and preview text
   - `/analyze/morph` - Morphological analysis
   - `/word-freq` - Word frequency analysis
   - `/group-words` - Similarity-based word grouping
   - `/analyze/theme-summary` - Theme summarization

2. **Data Management**:
   - `/ingest/post-answers` - Migrate data from posts table
   - `/report/summary` - Generate analysis reports

### Database Schema
The database uses a complex LMS schema with 20+ tables. Key entities:
- **Organizations**: Multi-tenant isolation
- **Profiles**: User management with roles (user/teacher/admin)
- **Journeys & Missions**: Content structure
- **Posts & Answers**: Student submissions
- **Files**: Centralized file management

See `specs/full-supabase-schema.md` for complete schema details.

### Caching Strategy
- Use Redis for caching analysis results
- Cache key format: `{org_id}:{journey_id}:{analysis_type}:{params_hash}`
- TTL: 7 days for analysis results
- Store persistent results in Supabase `text_analysis_cache` table

### NLP Processing Pipeline
1. Text normalization (remove special characters, normalize whitespace)
2. Morphological analysis using Okt
3. POS filtering (keep only meaningful parts of speech)
4. Stop word removal
5. Frequency analysis with configurable thresholds
6. Word grouping using similarity metrics

### Security Considerations
- All endpoints require JWT authentication
- Organization-based data isolation using RLS
- Role-based access control (user → teacher → admin)
- Validate file uploads (size, type)
- Sanitize text inputs before processing

### Performance Requirements
- Cache hit response: < 200ms
- Cache miss response: < 2.5s
- Word frequency limit: 30-50 words
- Max text length: 2000 characters

## Important Implementation Notes

1. **Korean Text Processing**: Use Okt for morphological analysis. Handle Korean-specific text normalization.

2. **Error Handling**: Implement comprehensive error handling with proper HTTP status codes and error messages in both Korean and English.

3. **Logging**: Use structured logging with request IDs for tracing.

4. **Environment Variables**: Load from `.env.local` for local development. Required vars:
   - `REDIS_URL`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `PROJECT_ID`

5. **Testing**: Write tests for all endpoints, especially the NLP pipeline and caching logic.

6. **API Documentation**: FastAPI auto-generates OpenAPI docs at `/docs`

## Development Workflow

1. Check existing specifications in `specs/` directory before implementing features
2. Follow the API specification in `specs/api-spec.md` for endpoint implementation
3. Use the database schema in `specs/full-supabase-schema.md` as reference
4. Implement proper error handling and validation for all endpoints
5. Add appropriate caching for expensive operations
6. Write tests alongside implementation
7. Update API documentation as needed

## Next Implementation Steps

1. Set up project structure with proper directories
2. Create requirements.txt with necessary dependencies
3. Implement core configuration and database connections
4. Build authentication middleware
5. Create base models matching the database schema
6. Implement the text analysis pipeline endpoints
7. Add caching layer with Redis
8. Write comprehensive tests
9. Set up Docker configuration for deployment

## Development and Deployment Guidelines

- Always follow the ultimate guideline for deployment and building project
- Refer to `@specs/DEVELOPMENT_CHECKLIST.md` for a comprehensive checklist
- Important steps:
  - Follow the checklist in order
  - After completing each todo item, modify the document and mark it as checked

### Supabase Monitoring & Management
- **Supabase MCP Integration**:
  - Use supabase-monster MCP to modify database, storage, or database policies
  - Inspect and implicate MCP usage for user-requested actions
  - Project ID: `egptutozdfchliouephl`
  - Always verify if a specific database or storage action requires MCP intervention