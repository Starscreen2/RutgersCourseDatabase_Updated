import requests
import logging
from datetime import datetime
from typing import Optional, List, Dict
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class CourseFetcher:
    def __init__(self):
        self.courses = []
        self.last_update = None
        self.base_url = "https://classes.rutgers.edu/soc/api/courses.json"

        # Configure requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

        self.update_courses()  # Initial fetch

    def convert_to_am_pm(self, military_time: str) -> str:
        """Convert military time to AM/PM format"""
        if not military_time or military_time == "N/A":
            return "N/A"
        try:
            return datetime.strptime(military_time, "%H%M").strftime("%I:%M %p")
        except ValueError:
            logger.warning(f"Invalid military time format: {military_time}")
            return "N/A"

    def format_meeting_time(self, meeting: Dict) -> Dict:
        """Format meeting time information"""
        try:
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
        except Exception as e:
            logger.error(f"Error formatting meeting time: {str(e)}")
            return {
                "day": "N/A",
                "start_time": {"military": "N/A", "formatted": "N/A"},
                "end_time": {"military": "N/A", "formatted": "N/A"},
                "building": "N/A",
                "room": "N/A",
                "mode": "N/A",
                "campus": "N/A"
            }

    def format_section(self, section: Dict) -> Dict:
        """Format section information with detailed meeting times"""
        try:
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
        except Exception as e:
            logger.error(f"Error formatting section: {str(e)}")
            return {
                "number": "Error",
                "index": "",
                "instructors": [],
                "status": "Error loading section",
                "comments": "",
                "meeting_times": []
            }

    def update_courses(self) -> None:
        """Fetch fresh course data from Rutgers API"""
        try:
            params = {
                "year": "2025",
                "term": "1",
                "campus": "NB"
            }
            logger.info(f"Fetching courses with parameters: {params}")

            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            courses = response.json()
            response_size = len(response.content) / 1024  # Size in KB
            logger.info(f"Retrieved {len(courses)} courses from API (Response size: {response_size:.2f} KB)")

            if not courses:
                logger.warning("Received empty course list from API")
                return

            # Log a sample course to verify structure
            if courses:
                logger.debug(f"Sample course structure: {json.dumps(courses[0], indent=2)}")

            self.courses = sorted(courses, key=lambda c: c.get("courseString", ""))
            self.last_update = datetime.now().isoformat()
            logger.info(f"Successfully updated courses at {self.last_update}")

        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching courses from API")
            if not self.courses:
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch courses from API: {str(e)}")
            if not self.courses:
                raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            if not self.courses:
                raise
        except Exception as e:
            logger.error(f"Unexpected error updating courses: {str(e)}")
            if not self.courses:
                raise

    def get_courses(self, subject: Optional[str] = None, course_number: Optional[str] = None, name: Optional[str] = None) -> List[Dict]:
        """Get filtered course data with enriched information"""
        try:
            if not self.courses:
                logger.warning("No courses available")
                return []

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
                # First get courses where title matches
                title_matches = [
                    course for course in filtered_courses
                    if name_lower in course.get("title", "").lower()
                ]
                # Then get other matches (subject/description) that weren't already matched by title
                other_matches = [
                    course for course in filtered_courses
                    if course not in title_matches and (
                        name_lower in course.get("subject", "").lower() or
                        name_lower in course.get("subjectDescription", "").lower()
                    )
                ]
                filtered_courses = title_matches + other_matches

            # Enrich course data with detailed information
            enriched_courses = []
            for course in filtered_courses:
                try:
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
                except Exception as e:
                    logger.error(f"Error enriching course data: {str(e)}")
                    continue

            logger.info(f"Returning {len(enriched_courses)} enriched courses for search: subject='{subject}', course_number='{course_number}', name='{name}'")
            return enriched_courses
        except Exception as e:
            logger.error(f"Error getting courses: {str(e)}")
            return []