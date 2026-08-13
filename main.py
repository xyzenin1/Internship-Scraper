import csv
import requests
from bs4 import BeautifulSoup
import json

from dotenv import load_dotenv
import os
from email.mime.text import MIMEText
import smtplib

import time

import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import ValidationConditionType

load_dotenv()


CARRIER_GATEWAYS = {
    "att": "txt.att.net",
    "verizon": "vtext.com",
    "tmobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    "boost": "sms.myboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "uscellular": "email.uscc.net",
    "googlefi": "msg.fi.google.com",
}


SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
CARRIER = os.getenv("CARRIER")

print("DEBUG:", SMTP_EMAIL, PHONE_NUMBER, CARRIER)


def get_sms_gateway_address():
    if not PHONE_NUMBER or not CARRIER:
        return None
    domain = CARRIER_GATEWAYS.get(CARRIER.lower())
    if not domain:
        print(f"Unknown carrier '{CARRIER}' - check CARRIER_GATEWAYS keys")
        return None
    return f"{PHONE_NUMBER}@{domain}"


def send_text(body):
    gateway_address = get_sms_gateway_address()
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD or not gateway_address:
        print("Texting skipped -- missing SMTP_EMAIL, SMTP_APP_PASSWORD, PHONE_NUMBER, or CARRIER in .env")
        return

    msg = MIMEText(body)
    msg["From"] = SMTP_EMAIL
    msg["To"] = gateway_address
    msg["Subject"] = ""  # most carrier gateways ignore/prepend the subject, keep it blank

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(SMTP_EMAIL, gateway_address, msg.as_string())
        print(f"Text sent to {gateway_address}")
    except Exception as e:
        print(f"Failed to send text: {e}")






def send_new_job_texts(jobs, chunk_size=300, delay_seconds=3):
    # Splits into multiple texts if the list is long
    # If message is too long, it might get rejected
    header = f"{len(jobs)} new matching internships:\n"
    body = header
    chunks = []
    for job in jobs:
        line = f"{job['company']} - {job['role']} - {job['location']}\n"
        if len(body) + len(line) > chunk_size:
            chunks.append(body)
            body = ""
        body += line
    if body.strip():
        chunks.append(body)
        
    for i, chunk in enumerate(chunks):
        send_text(chunk)
        if i < len(chunks) - 1:
            time.sleep(delay_seconds)









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


# user input to decide location
user_input = input("Choose 1 for all locations, 2 for Arizona Only, or 3 for a location of your choice: ")
jobs_to_show = 0

while True:
    try:
        choice = int(user_input)
    except ValueError:
        print("Not a valid input! Please enter 1, 2, or 3.")
        user_input = input("Choose 1 for all locations, 2 for Arizona Only, or 3 for a location of your choice: ")
        continue

    if choice == 1:
        jobs_to_show = all_jobs
        
        for job in all_jobs:
            print(f"{job['company']} - {job['role']} - {job['location']} - {job['link']}")
        break
    elif choice == 2:
        jobs_to_show = location_jobs
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
        
        
        break
    
    elif choice == 3:
        user_location_choice = input("Type in a location (ex. Phoenix, AZ) (ex. IL): ").strip()
        custom_locations = [job for job in all_jobs
                        if user_location_choice.lower() in job["location"].lower()
                        ]
        
        jobs_to_show = custom_locations
        
        # checks to see if input is found in list, if not then loop again
        if len(jobs_to_show) == 0:
            print(f"No internships found! Try again!")
            user_input = input("Choose 1 for all locations, 2 for Arizona Only, or 3 for a location of your choice: ")

            continue
    
        for job in jobs_to_show:
            print(f"{job['company']} - {job['role']} - {job['location']} - {job['link']}")
        
        break
    else:
        print("Not a valid input! Please enter 1, 2, or 3.")
        user_input = input("Choose 1 for all locations, 2 for Arizona Only, or 3 for a location of your choice: ")





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
    print(f"DEBUG: successfully read {len(existing_records)} existing rows")
except Exception as e:
    print(f"DEBUG: get_all_records failed with: {e}")
    existing_records = []
    
def to_bool(value):
    return str(value).strip().upper() == "TRUE"
    

applied_status = {
    row["link"]: to_bool(row.get("applied", False))
    for row in existing_records
    if row.get("link")
}

# check if the posting was seen before
previously_seen_links = set(applied_status.keys())




if len(jobs_to_show) == 0:
    print("No jobs to write -- skipping Google Sheets update to avoid wiping existing data.")
else:
    sheet.clear()
    sheet.append_row(["category", "company", "role", "location", "link", "applied", "Seen"], value_input_option="USER_ENTERED")


    
    def to_sheet_bool(value):
        return "TRUE" if value else "FALSE"
    
    
    rows_to_write = [
        [
            job["category"], job["company"], job["role"], job["location"], job["link"],
            to_sheet_bool(applied_status.get(job["link"], False)),  # default unchecked for new jobs, but keep old status
            to_sheet_bool(job["link"] in previously_seen_links),   # return true if the posting was never seen before
        ]
        for job in jobs_to_show  # show listings
    ]

    sheet.append_rows(rows_to_write, value_input_option="USER_ENTERED")

    last_row = len(rows_to_write) + 1  # +1 for header row

    sheet.add_validation(
        f"F2:F{last_row}",   # last column is now listed as applied
        ValidationConditionType.boolean,        # checkmark boxes instead of just saying TRUE or FALSE
        [],
    )

    # Checks for new
    sheet.add_validation(
        f"G2:G{last_row}",
        ValidationConditionType.boolean, 
        [],
    )

    # increment count if a new posting is recorded
    new_count = sum(1 for row in rows_to_write if not row[6])
    print(f"{new_count} new internships since last run")
    
    
    def matches_filters(job):
        role_lower = job["role"].lower()
        category = job.get("category") or ""
        if any(kw in role_lower for kw in cyber_keywords):
            return True
        if any(kw in role_lower for kw in swe_keywords):
            return True
        if "Data Science" in category:
            return True
        if "Product Management" in category:
            return True
        return False
    
    new_matching_jobs = [
        job for job in jobs_to_show
        if job["link"] not in previously_seen_links and matches_filters(job)
    ]

    if new_matching_jobs:
        print(f"Texting {len(new_matching_jobs)} new listing that match your filters: ")
        send_new_job_texts(new_matching_jobs)
    else:
        print("No new listings matched your filters")
