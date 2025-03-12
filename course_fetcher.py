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
        # Define param_key before the try block to make it available in exception handlers
        param_key = f"{year}_{term}_{campus}"
        
        try:
            params = {"year": year, "term": term, "campus": campus}
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
        
        # Check if query matches common patterns for course codes
        is_specific_course_query = False
        subject_part = None
        number_part = None
        
        # Pattern matching for queries like "cs 111", "198:111", "computer science 111"
        # Common department abbreviations
        dept_abbrevs = {
            "cs": "198",  # Computer Science
            "math": "640",  # Mathematics
            "bio": "119",  # Biology
            "chem": "160",  # Chemistry
            "phys": "750",  # Physics
            "stat": "960",  # Statistics
            "econ": "220"   # Economics
        }
        
        # Try to parse common query formats
        query_parts = query.split()
        if len(query_parts) == 2:
            # Format like "cs 111" or "math 152"
            potential_dept, potential_number = query_parts
            if potential_number.isdigit():
                is_specific_course_query = True
                subject_part = dept_abbrevs.get(potential_dept, potential_dept)
                number_part = potential_number
        elif ":" in query:
            # Format like "198:111"
            parts = query.split(":")
            if len(parts) == 2 and parts[1].isdigit():
                is_specific_course_query = True
                subject_part = parts[0]
                number_part = parts[1]
        elif query.isdigit():
            # Just a course number like "111"
            is_specific_course_query = True
            number_part = query
        
        # Group courses by their course_string for consistent matching
        course_groups = {}
        exact_matches = []
        high_relevance_matches = []
        
        # Process all courses
        for course in courses:
            course_string = course.get("courseString", "").lower()
            subject = course.get("subject", "").lower()
            course_number = course.get("courseNumber", "").lower()
            title = course.get("title", "").lower()
            subject_description = course.get("subjectDescription", "").lower()
            
            # Store courses by their courseString for grouping
            if course_string not in course_groups:
                course_groups[course_string] = []
            course_groups[course_string].append(course)
            
            # Special handling for CS (Computer Science) department
            # Common mistake: "cs" searches matching many unrelated courses
            if query == "cs" and subject != "198":
                continue
                
            # Handle specific course query patterns
            if is_specific_course_query:
                # Perfect match on subject and course number
                if (subject_part and number_part and 
                    subject == subject_part and course_number == number_part):
                    exact_matches.append((100, course_string))
                    continue
                    
                # Match on just the course number if that's all we have
                elif (not subject_part and number_part and
                     course_number == number_part):
                    exact_matches.append((95, course_string))
                    continue
                    
                # For dept abbreviation matches like "cs" -> "Computer Science"
                elif (subject_part in dept_abbrevs.keys() and 
                      number_part and 
                      subject == "198" and  # CS department code
                      course_number == number_part):
                    exact_matches.append((98, course_string))
                    continue
                
                # For matches on subject description like "computer science"
                elif (subject_part and number_part and 
                      subject_part in subject_description and 
                      course_number == number_part):
                    high_relevance_matches.append((90, course_string))
                    continue
            
            # Case 1: Exact match on course code
            if query == course_string or query == f"{subject}:{course_number}":
                exact_matches.append((100, course_string))
                continue
            
            # Case 2: Exact match on just course number or subject
            if query == course_number or query == subject:
                high_relevance_matches.append((85, course_string))
                continue
                
            # Skip fuzzy matching if we're doing a specific course search
            # This prevents unrelated courses from showing up
            if is_specific_course_query:
                continue
            
            # Case 3: Fuzzy matching for general searches
            score_course_string = fuzz.token_set_ratio(query, course_string)
            score_title = fuzz.token_set_ratio(query, title)
            score_subject = fuzz.token_set_ratio(query, subject)
            score_course_number = fuzz.token_set_ratio(query, course_number)
            score_subject_desc = fuzz.token_set_ratio(query, subject_description)

            max_score = max(score_course_string, score_title, score_subject,
                            score_course_number, score_subject_desc)
                            
            if max_score >= threshold:
                results.append((max_score, course_string))

        # Create a unique set of course strings that matched
        unique_results = {}
        
        # First add exact matches with highest priority
        for score, course_string in exact_matches:
            unique_results[course_string] = score
            
        # Then add high relevance matches
        for score, course_string in high_relevance_matches:
            if course_string not in unique_results or score > unique_results[course_string]:
                unique_results[course_string] = score
        
        # Then add fuzzy matches with lowest priority
        if not is_specific_course_query or len(unique_results) == 0:
            for score, course_string in results:
                if course_string not in unique_results or score > unique_results[course_string]:
                    unique_results[course_string] = score
        
        # Convert back to list and sort by score
        sorted_results = sorted([(score, cs) for cs, score in unique_results.items()], 
                               key=lambda x: x[0], reverse=True)
        
        # Get all courses for each matched course string
        matched_courses = []
        for _, course_string in sorted_results:
            matched_courses.extend(course_groups.get(course_string, []))
            
        logger.info(f"Search for '{query}' found {len(matched_courses)} courses from {len(unique_results)} unique course strings")
        return matched_courses

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
                        "courseString": course.get("courseString", ""),
                        "title": course.get("title", ""),
                        "subject": course.get("subject", ""),
                        "subjectDescription": course.get("subjectDescription", ""),
                        "course_number": course.get("courseNumber", ""),
                        "description": course.get("courseDescription", ""),
                        "credits": course.get("credits", ""),
                        "creditsDescription": course.get("creditsObject", {}).get("description", ""),
                        "school": course.get("school", {}).get("description", ""),
                        "campusLocations": [
                            loc.get("description", "") for loc in course.get("campusLocations", [])
                        ],
                        "prerequisites": course.get("preReqNotes", ""),
                        "coreRequirements": [
                            {
                                "code": core.get("coreCode", ""),
                                "description": core.get("coreCodeDescription", "")
                            }
                            for core in course.get("coreCodes", [])
                        ],
                        "sections": [
                            self.format_section(section) for section in course.get("sections", [])
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
