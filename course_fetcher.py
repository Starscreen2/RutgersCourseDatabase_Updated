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

    def convert_to_am_pm(self, military_time: str) -> str:
        """Convert military time to AM/PM format"""
        if not military_time or military_time == "N/A":
            return "N/A"
        try:
            return datetime.strptime(military_time, "%H%M").strftime("%I:%M %p")
        except ValueError:
            return "N/A"

    def format_meeting_time(self, meeting: Dict) -> Dict:
        """Format meeting time information"""
        start_time = meeting.get("startTimeMilitary", "N/A")
        end_time = meeting.get("endTimeMilitary", "N/A")

        return {
            "day": meeting.get("meetingDay", ""),
            "start_time": {
                "military": start_time,
                "formatted": self.convert_to_am_pm(start_time)
            },
            "end_time": {
                "military": end_time,
                "formatted": self.convert_to_am_pm(end_time)
            },
            "building": meeting.get("buildingCode", "N/A"),
            "room": meeting.get("roomNumber", "N/A"),
            "mode": meeting.get("meetingModeDesc", "N/A"),
            "campus": meeting.get("campusLocation", "N/A")
        }

    def format_section(self, section: Dict) -> Dict:
        """Format section information with detailed meeting times"""
        return {
            "number": section.get("number", ""),
            "index": section.get("index", ""),
            "instructors": [instr.get("name", "") for instr in section.get("instructors", [])],
            "status": section.get("openStatusText", ""),
            "comments": section.get("commentsText", ""),
            "meeting_times": [
                self.format_meeting_time(meeting)
                for meeting in section.get("meetingTimes", [])
            ]
        }

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

            courses = response.json()
            logger.debug(f"Retrieved {len(courses)} courses from API")

            self.courses = sorted(courses, key=lambda c: c.get("courseString", ""))
            self.last_update = datetime.now().isoformat()
            logger.info(f"Successfully updated courses at {self.last_update}")
        except Exception as e:
            logger.error(f"Failed to update courses: {str(e)}")
            if not self.courses:  # Only raise if we have no data at all
                raise

    def get_courses(self, subject: Optional[str] = None, course_number: Optional[str] = None, name: Optional[str] = None) -> List[Dict]:
        """Get filtered course data with enriched information"""
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

        # Enrich course data with detailed information
        enriched_courses = []
        for course in filtered_courses:
            enriched_course = {
                "courseString": course.get("courseString", ""),
                "title": course.get("title", ""),
                "subject": course.get("subject", ""),
                "subjectDescription": course.get("subjectDescription", ""),
                "courseNumber": course.get("courseNumber", ""),
                "credits": course.get("credits", ""),
                "creditsDescription": course.get("creditsObject", {}).get("description", ""),
                "school": course.get("school", {}).get("description", ""),
                "campusLocations": [loc.get("description", "") for loc in course.get("campusLocations", [])],
                "prerequisites": course.get("preReqNotes", ""),
                "coreRequirements": [
                    {
                        "code": core.get("coreCode", ""),
                        "description": core.get("coreCodeDescription", "")
                    }
                    for core in course.get("coreCodes", [])
                ],
                "sections": [
                    self.format_section(section)
                    for section in course.get("sections", [])
                ]
            }
            enriched_courses.append(enriched_course)

        logger.debug(f"Returning {len(enriched_courses)} enriched courses")
        return enriched_courses