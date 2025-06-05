[Rutgers Course Search](https://rutgers.replit.app/)

## Features
- Real-time course data from Rutgers API
- Search by title, subject, or course number
- Filter by year, term, and campus
- Detailed course info (sections, times, instructors, etc.)
- Detailed classroom search (sections, times, instructors, occupancy, ect.)

## Tech Stack
- Backend: Flask (Python 3.11)
- Frontend: Bootstrap 5.3
- Rate Limiting & Caching

## API Endpoints
- GET /api/courses: Get course info with filters
- GET /api/health: Check API status

## Rate Limits
- 200 requests/day
- 50 requests/hour
- 30 requests/minute for /api/courses

## Running Locally
```bash
python main.py  # Development (port 5000)

Structure
/app.py: Main Flask app
/course_fetcher.py: Data processing
/templates/: HTML templates
/static/: Assets
