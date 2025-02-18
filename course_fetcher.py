import requests
import logging
from datetime import datetime
from typing import Optional, List, Dict
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class CourseFetcher:
    # Mapping weekday codes to full names
    WEEKDAY_MAP = {
        "M": "Monday",
        "T": "Tuesday",
        "W": "Wednesday",
        "H": "Thursday",
        "F": "Friday",
        "S": "Saturday",
        "Su": "Sunday"
    }

    # Mapping campus IDs to campus names
    CAMPUS_MAP = {
        "1": "College Ave",
        "2": "Busch",
        "3": "Livingston",
        "4": "Cook/Doug"
    }

    def __init__(self):
        self.courses_by_params = {
        }  # Store courses for different parameter combinations
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

        self.update_courses()  # Initial fetch with default params

    def convert_to_am_pm(self, military_time: str) -> str:
        """Convert military time to AM/PM format"""
        if not military_time or military_time == "N/A":
            return "N/A"
        try:
            return datetime.strptime(military_time,
                                     "%H%M").strftime("%I:%M %p").lstrip("0")
        except ValueError:
            logger.warning(f"Invalid military time format: {military_time}")
            return "N/A"

    def format_weekday(self, day: str) -> str:
        """Convert weekday code to full name"""
        return self.WEEKDAY_MAP.get(day, day)

    def format_campus(self, campus_id: str) -> str:
        """Convert campus ID to campus name"""
        return self.CAMPUS_MAP.get(campus_id, campus_id)

    def format_meeting_time(self, meeting: Dict) -> Dict:
        """Format meeting time information with proper weekday and campus names"""
        try:
            start_time = meeting.get("startTimeMilitary", "N/A")
            end_time = meeting.get("endTimeMilitary", "N/A")
            day_code = meeting.get("meetingDay", "")
            campus_id = meeting.get("campusLocation", "N/A")

            return {
                "day": self.format_weekday(day_code),
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
                "campus": self.format_campus(campus_id)
            }
        except Exception as e:
            logger.error(f"Error formatting meeting time: {str(e)}")
            return {
                "day": "N/A",
                "start_time": {
                    "military": "N/A",
                    "formatted": "N/A"
                },
                "end_time": {
                    "military": "N/A",
                    "formatted": "N/A"
                },
                "building": "N/A",
                "room": "N/A",
                "mode": "N/A",
                "campus": "N/A"
            }

    def format_section(self, section: Dict) -> Dict:
        """Format section information with detailed meeting times"""
        try:
            return {
                "number":
                section.get("number", ""),
                "index":
                section.get("index", ""),
                "instructors": [
                    instr.get("name", "")
                    for instr in section.get("instructors", [])
                ],
                "status":
                section.get("openStatusText", ""),
                "comments":
                section.get("commentsText", ""),
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

    def update_courses(self, year="2025", term="1", campus="NB") -> None:
        """Fetch fresh course data from Rutgers API"""
        try:
            params = {"year": year, "term": term, "campus": campus}
            param_key = f"{year}_{term}_{campus}"

            logger.info(f"Fetching courses with parameters: {params}")

            response = self.session.get(self.base_url,
                                        params=params,
                                        timeout=30)
            response.raise_for_status()

            courses = response.json()
            response_size = len(response.content) / 1024  # Size in KB
            logger.info(
                f"Retrieved {len(courses)} courses from API (Response size: {response_size:.2f} KB)"
            )

            if not courses:
                logger.warning("Received empty course list from API")
                return

            # Log a sample course to verify structure
            if courses:
                logger.debug(
                    f"Sample course structure: {json.dumps(courses[0], indent=2)}"
                )

            self.courses_by_params[param_key] = sorted(
                courses, key=lambda c: c.get("courseString", ""))
            self.last_update = datetime.now().isoformat()
            logger.info(f"Successfully updated courses at {self.last_update}")

        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching courses from API")
            if param_key not in self.courses_by_params:
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch courses from API: {str(e)}")
            if param_key not in self.courses_by_params:
                raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            if param_key not in self.courses_by_params:
                raise
        except Exception as e:
            logger.error(f"Unexpected error updating courses: {str(e)}")
            if param_key not in self.courses_by_params:
                raise

    def fuzzy_search_courses(self,
                             courses: List[Dict],
                             query: str,
                             threshold: int = 70) -> List[Dict]:
        """Filter and rank courses using fuzzy matching on key fields."""
        results = []
        query = query.lower().strip()
        for course in courses:
            course_string = course.get("courseString", "").lower()
            title = course.get("title", "").lower()
            subject = course.get("subject", "").lower()
            course_number = course.get("courseNumber", "").lower()

            score_course_string = fuzz.token_set_ratio(query, course_string)
            score_title = fuzz.token_set_ratio(query, title)
            score_subject = fuzz.token_set_ratio(query, subject)
            score_course_number = fuzz.token_set_ratio(query, course_number)

            max_score = max(score_course_string, score_title, score_subject,
                            score_course_number)
            if max_score >= threshold:
                results.append((max_score, course))

        # Sort by score descending for best matches
        results.sort(key=lambda x: x[0], reverse=True)
        return [course for score, course in results]

    def get_courses(self,
                    search: Optional[str] = None,
                    year="2025",
                    term="1",
                    campus="NB") -> List[Dict]:
        """Get filtered course data with enriched information and fuzzy search."""
        try:
            param_key = f"{year}_{term}_{campus}"

            # Update courses for these parameters if not already cached
            if param_key not in self.courses_by_params:
                self.update_courses(year, term, campus)

            if not self.courses_by_params.get(param_key):
                logger.warning(
                    f"No courses available for parameters: year={year}, term={term}, campus={campus}"
                )
                return []

            filtered_courses = self.courses_by_params[param_key]

            if search:
                # Use fuzzy search to filter courses
                filtered_courses = self.fuzzy_search_courses(
                    filtered_courses, search)

            # Enrich course data with detailed information
            enriched_courses = []
            for course in filtered_courses:
                try:
                    enriched_course = {
                        "courseString":
                        course.get("courseString", ""),
                        "title":
                        course.get("title", ""),
                        "subject":
                        course.get("subject", ""),
                        "subjectDescription":
                        course.get("subjectDescription", ""),
                        "course_number":
                        course.get("courseNumber", ""),
                        "description":
                        course.get("courseDescription", ""),
                        "credits":
                        course.get("credits", ""),
                        "creditsDescription":
                        course.get("creditsObject", {}).get("description", ""),
                        "school":
                        course.get("school", {}).get("description", ""),
                        "campusLocations": [
                            loc.get("description", "")
                            for loc in course.get("campusLocations", [])
                        ],
                        "prerequisites":
                        course.get("preReqNotes", ""),
                        "coreRequirements": [{
                            "code":
                            core.get("coreCode", ""),
                            "description":
                            core.get("coreCodeDescription", "")
                        } for core in course.get("coreCodes", [])],
                        "sections": [
                            self.format_section(section)
                            for section in course.get("sections", [])
                        ]
                    }
                    enriched_courses.append(enriched_course)
                except Exception as e:
                    logger.error(f"Error enriching course data: {str(e)}")
                    continue

            logger.info(
                f"Returning {len(enriched_courses)} enriched courses for search: '{search}'"
            )
            return enriched_courses
        except Exception as e:
            logger.error(f"Error getting courses: {str(e)}")
            return []
