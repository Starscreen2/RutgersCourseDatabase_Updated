# Rutgers Course Search

https://rutgers.replit.app/

A Flask-based web application for searching Rutgers University course and instructor salary information in real-time.

## Features
- Real-time course data from Rutgers API
- Instructor salary lookup via a hover tooltip (NEW)
- Search by title, subject, or course number
- Filter by year, term, and campus
- Detailed course info (sections, times, instructors, etc.)

## Tech Stack
- Backend: Flask (Python 3.11)
- Frontend: Bootstrap 5.3
- Rate Limiting & Caching

## API Endpoints
- GET /api/courses: Get course info with filters
- GET /api/salary: Retrieves salary data for an instructor (NEW)
- GET /api/health: Check API status

## Rate Limits
- Adequate

Structure
/app.py                 # Main Flask app
/salary_api.py          # Instructor salary processing (NEW)
/course_fetcher.py      # Course data processing
/static/                # Assets (CSS, JavaScript)
/templates/             # HTML templates


🎯 Want to Contribute?
Pull requests and suggestions are welcome! 🎉

🔥 Try it out and let me know what you think! 🚀

