import os
from flask import Flask, jsonify, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from apscheduler.schedulers.background import BackgroundScheduler
from course_fetcher import CourseFetcher
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Initialize course fetcher
course_fetcher = CourseFetcher()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=course_fetcher.update_courses, trigger="interval", minutes=15)
scheduler.start()

@app.route('/api/health')
@limiter.exempt
def health_check():
    return jsonify({
        "status": "healthy",
        "last_update": course_fetcher.last_update
    })

@app.route('/api/courses')
@limiter.limit("30 per minute")
@cache.cached(timeout=60)
def get_courses():
    try:
        subject = request.args.get('subject')
        course_number = request.args.get('course_number')
        name = request.args.get('name')

        courses = course_fetcher.get_courses(subject, course_number, name)
        return jsonify({
            "status": "success",
            "data": courses,
            "last_update": course_fetcher.last_update
        })
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to fetch course data"
        }), 500

@app.route('/')
def docs():
    return send_from_directory('static', 'docs.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "status": "error",
        "message": "Rate limit exceeded"
    }), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)