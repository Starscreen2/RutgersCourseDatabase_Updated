import requests
from bs4 import BeautifulSoup
import csv
import time

# URL of the Rutgers SAS Majors and Minors page
main_url = "https://sasundergrad.rutgers.edu/majors-and-core-curriculum/major/list-of-majors-and-minors"

# Send HTTP GET request
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(main_url, headers=headers)

# Check if the request was successful
if response.status_code != 200:
    print(f"❌ Failed to fetch the main webpage. Status code: {response.status_code}")
    exit()

soup = BeautifulSoup(response.text, "html.parser")

# Extract all rows in the table
majors_minors_data = []

for row in soup.select("tbody tr.latestnews-item"):
    try:
        # Extract major/minor name and link
        title_tag = row.select_one("td[data-title='Major / Minor'] a")
        major_minor_name = title_tag.get_text(strip=True) if title_tag else "N/A"
        major_minor_link = title_tag["href"] if title_tag else "N/A"

        # Extract school name
        school_tag = row.select_one("td[data-title='School'] span.detail_data")
        school_name = school_tag.get_text(strip=True) if school_tag else "N/A"

        # Extract advising page URL
        advising_tag = row.select_one("td[data-title='Advising Page'] a")
        advising_text = advising_tag.get_text(strip=True) if advising_tag else "N/A"
        advising_link = advising_tag["href"] if advising_tag else "N/A"

        # Store data
        majors_minors_data.append([major_minor_name, f"https://sasundergrad.rutgers.edu{major_minor_link}", school_name, advising_text, advising_link])

    except Exception as e:
        print(f"⚠️ Error parsing a row: {e}")

# Define headers for the output CSV
output_csv = "majors_minors_requirements.csv"
output_headers = ["Major/Minor", "Major/Minor URL", "School", "Advising Page Name", "Advising Page URL", "Requirement for Major Declaration"]

# Open the output CSV for writing
with open(output_csv, "w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerow(output_headers)  # Write header row

    # Loop through each major/minor URL to scrape the requirement details
    for entry in majors_minors_data:
        major_name, major_url, school_name, advising_text, advising_link = entry

        print(f"Scraping: {major_url}")

        # Send request with User-Agent
        try:
            response = requests.get(major_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"⚠️ Error fetching {major_url}: {e}")
            writer.writerow([major_name, major_url, school_name, advising_text, advising_link, "Failed to fetch"])
            continue

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all collapsible sections
        collapsibles = soup.find_all("a", class_="collapsible")

        requirement_text = "Not Found"
        for section in collapsibles:
            if section.text.strip().startswith("Requirement for Major Declaration"):  # Handle spaces
                collapse_id = section["href"].replace("#", "")

                # Find the corresponding div with the collapse ID
                collapse_div = soup.find("div", id=collapse_id)
                if collapse_div:
                    span_text = collapse_div.find("span", class_="field-value")
                    if span_text:
                        requirement_text = span_text.get_text(" ", strip=True)  # Preserve formatting
                break  # Stop after finding the correct section

        # Write data to CSV
        writer.writerow([major_name, major_url, school_name, advising_text, advising_link, requirement_text])

        # Respectful scraping - wait before the next request
        time.sleep(1.5)

print(f"\n✅ Done! Data saved in '{output_csv}'.")
