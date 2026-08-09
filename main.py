import csv
import requests
from bs4 import BeautifulSoup
import json

from dotenv import load_dotenv
import os

import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import ValidationConditionType

load_dotenv()


url = "https://github.com/SimplifyJobs/Summer2027-Internships"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout = 15)
print(response.status_code)     # 200 is good

# parses the html string so we can now search
soup = BeautifulSoup(response.text, "html.parser")

article = soup.find("article", class_="markdown-body")

tables = article.find_all("table")
print(len(tables))      # category tables


print(os.path.exists("service_account.json"))


#print out tables
# table = tables[0]
# rows = table.find_all("tr")

# for row in rows[1:]:
#     cells = row.find_all("td")
#     company = cells[0].get_text(strip=True)
#     role = cells[1].get_text(strip=True)
#     location = cells[2].get_text(strip=True)
#     print(company, "-", role)
    

    
current_heading = None
all_jobs = []


for el in article.find_all(["h2", "h3", "table"]):
    if el.name in ("h2", "h3"):
        current_heading = el.get_text(strip=True)
    else:
        rows = el.find_all("tr")
        for row in rows[1:]:        # account for the header
            cells = row.find_all("td")
            
            # if a row is incomplete
            if len(cells) < 4:
                continue
            
            company = cells[0].get_text(strip=True)
            role = cells[1].get_text(strip=True)
            location = cells[2].get_text(separator=", ", strip=True)
            
            #   find link for internships
            link_tag = cells[3].find("a")
            if link_tag:
                link = link_tag["href"]
            else:
                link = ""
                
            all_jobs.append({
                "category": current_heading,
                "company": company,
                "role": role,
                "location": location,
                "link": link
            })


# filter for locations
arizona_locations = [", AZ", "Phoenix", "Tempe", "Scottsdale", "Chandler", "Mesa", "Tucson"]

# filter for locations the user chooses
# chosen_location = input("Choose the city/state (ex. Seattle, WA): ")


#filter for cybersecurity
cyber_keywords = ["security", "cyber", "soc analyst", "infosec", "penetration", "vuln"]
# filter for swe
swe_keywords = [
    "software engineer", "software developer", "software development",
    "backend", "back-end", "frontend", "front-end", "full-stack", "full stack",
    "sde", "swe", "web developer", "application developer",
    "mobile developer", "ios developer", "android developer",
    "platform engineer", "infrastructure engineer", "site reliability",
]


location_jobs = [job for job in all_jobs
                 if any(loc in job["location"] for loc in arizona_locations)
                 ]

print(f"{len(location_jobs)} Arizona Internships Found")
for job in location_jobs:
    print(f"{job['company']} - {job['role']} - {job['location']} - {job['link']}")
    
cyber_jobs = [job for job in location_jobs
                if any(kw in job["role"].lower() for kw in cyber_keywords)
                ]

print("")
print(f"{len(cyber_jobs)} match for cybersecurity")
if len(cyber_jobs) > 0:
    for job in cyber_jobs:
        print(f"{job['company']} - {job['role']} - {job['location']} - {job['link']}")
        
        

swe_jobs = [job for job in location_jobs
                if any(swe in job["role"].lower() for swe in swe_keywords)
            ]
    
    
    
print("")
print(f"{len(swe_jobs)} match for SWE")
if len(swe_jobs) > 0:
    for job in swe_jobs:
        print(f"{job['company']} - {job['role']} - {job['location']} - {job['link']}")

ds_jobs = [
        job for job in location_jobs
        if "Data Science" in job["category"]
    ]

print("")
print(f"{len(ds_jobs)} match for Data Science")
if len(ds_jobs) > 0:
    for job in location_jobs:
        print(f"{job['company']} - {job['role']} - {job['location']} - {job['link']}")
        
pm_jobs = [
        job for job in location_jobs
        if "Product Management" in job["category"]
    ]

print("")
print(f"{len(pm_jobs)} match for Product Management")
if len(pm_jobs) > 0:
    for job in location_jobs:
        print(f"{job['company']} - {job['role']} - {job['location']} - {job['link']}")
            


with open("internships.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["category", "company", "role", "location", "link"])
    writer.writeheader()
    writer.writerows(all_jobs)

# print all job lists
# print(f"Found {len(all_jobs)}")
# print(filtered_jobs)
            
    

# Google cloud api for spreadsheet
# Google Spreadsheet API and Google Drive API
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

EMAIL = os.getenv("SERVICE_EMAIL")


# safety net if names are not found
if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_NAME:
    raise RuntimeError("Missing .env values -- check that .env exists and has SERVICE_ACCOUNT_FILE and SPREADSHEET_NAME set")


# look for the internship email to share with spreadsheet
# with open("internship-project-504917-8bfa208c1f7b.json") as f:
#     data = json.load(f)
# print(data["client_email"])

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)


# open spreadsheet
# looks for a spreadsheet with the same name
spreadsheet = client.open(SPREADSHEET_NAME)

sheet = spreadsheet.sheet1



# check if you applied to listing already
try:
    existing_records = sheet.get_all_records()
except Exception:
    existing_records = []
    
applied_status = {
    row["link"]: row.get("applied", False)
    for row in existing_records
    if row.get("link")
}

sheet.clear()
sheet.append_row(["category", "company", "role", "location", "link", "applied"], value_input_option="USER_ENTERED")


rows_to_write = [
    [
        job["category"], job["company"], job["role"], job["location"], job["link"],
        applied_status.get(job["link"], False),  # default unchecked for new jobs, but keep old status
    ]
    for job in location_jobs  # show listings
]

sheet.append_rows(rows_to_write, value_input_option="USER_ENTERED")

last_row = len(rows_to_write) + 1  # +1 for header row
sheet.add_validation(
    f"F2:F{last_row}",   # last column is now listed as applied
    ValidationConditionType.boolean,        # checkmark boxes instead of just saying TRUE or FALSE
    [],
)
