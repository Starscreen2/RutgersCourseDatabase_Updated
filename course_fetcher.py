import requests
import logging
from datetime import datetime
from typing import Optional, List, Dict
import json

logger = logging.getLogger(__name__)

class CourseFetcher:
    def __init__(self):
        self.courses = []
        self.last_update = None
        self.base_url = "https://classes.rutgers.edu/soc/api/courses.json"
        self.update_courses()  # Initial fetch

    def update_courses(self) -> None:
        """Fetch fresh course data from Rutgers API"""
        try:
            params = {
                "year": "2024",
                "term": "9",
                "campus": "NB"
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            self.courses = sorted(response.json(), key=lambda c: c.get("courseString", ""))
            self.last_update = datetime.now().isoformat()
            logger.info(f"Successfully updated courses at {self.last_update}")
        except Exception as e:
            logger.error(f"Failed to update courses: {str(e)}")
            if not self.courses:  # Only raise if we have no data at all
                raise

    def get_courses(self, subject: Optional[str] = None, course_number: Optional[str] = None, name: Optional[str] = None) -> List[Dict]:
        """Get filtered course data"""
        filtered_courses = self.courses

        if subject:
            filtered_courses = [
                course for course in filtered_courses
                if course.get("subject", "").lower() == subject.lower()
            ]

        if course_number:
            filtered_courses = [
                course for course in filtered_courses
                if course.get("courseNumber", "") == course_number
            ]

        if name:
            name_lower = name.lower()
            filtered_courses = [
                course for course in filtered_courses
                if name_lower in course.get("title", "").lower()
            ]

        return filtered_courses