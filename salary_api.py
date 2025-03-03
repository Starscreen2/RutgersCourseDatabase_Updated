import os
import json
import csv

class SalaryData:
    """Handles loading and retrieving Rutgers instructor salaries."""

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(base_dir, "rutgers_salaries.csv")
        self.json_path = os.path.join(base_dir, "rutgers_salaries.json")
        self.salaries = self._load_salaries()

    def _load_salaries(self):
        """Loads salary data from CSV or JSON."""
        salaries = []

        if os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        cleaned_row = {key.strip(): value.strip() for key, value in row.items()}
                        salaries.append(cleaned_row)
                return salaries
            except Exception:
                pass

        elif os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as jsonfile:
                    salaries = json.load(jsonfile)
                return salaries
            except Exception:
                pass

        return []

    def get_all_salaries(self):
        """Returns all salaries."""
        return self.salaries

    def get_salary_by_instructor(self, name):
        """Search for an instructor's salary by name, handling different name formats, including single-word matches."""

        # Normalize function (strip spaces and convert to lowercase)
        def normalize(text):
            return text.lower().strip()

        # Convert "LAST, FIRST" to "First Last"
        def convert_last_first(name):
            parts = name.split(", ")
            return f"{parts[1]} {parts[0]}" if len(parts) == 2 else name

        normalized_name = normalize(name)
        converted_name = normalize(convert_last_first(name))

        print(f"🔎 Searching for: {normalized_name} OR {converted_name}")  # Debugging

        # Exact match search
        results = [
            entry for entry in self.salaries
            if normalize(entry.get("Name", "")) in [normalized_name, converted_name]
        ]

        if results:
            print(f"✅ Found exact match: {results[0]}")  # Debugging
            return results  # Return immediately if a match is found

        print("No exact match found! Performing secondary search...")  

        # Single-word name match (if the input is just one word)
        if " " not in normalized_name:  # Only do this if searching for a single-word name
            results = [
                entry for entry in self.salaries
                if normalized_name in normalize(entry.get("Name", "")).split()
            ]

            if results:
                print(f"✅ Found single-word match: {results[0]}")
                return results

        print("⚠️ No match found!")
        return None



