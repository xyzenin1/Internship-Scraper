# Internship Search
 
A Python script that searches for internships by scraping https://github.com/SimplifyJobs/Summer2027-Internships, which is the SimplifyJobs Summer Internships tracker on GitHub. After scraping, it will display the information on a google sheet.


## Setup
 
### 1. Install dependencies
 
pip install requests beautifulsoup4 gspread google-auth
pip install python-dotenv


### 2. Set up Google Sheets access
 
This is technically optional, since the csv is printed out in the terminal
 
1. Go to https://console.cloud.google.com/ and create a new project
2. Make sure you enable the **Google Sheets API** and **Google Drive API**
3. Go to **APIs & Services > Credentials > Create Credentials > Service account**
4. Open the service account, go to **Keys > Add Key > Create new key**, choose **JSON**
5. Save the downloaded `.json` file and move it to this project folder; Make sure main.py and .json are in the same folder
6. Create a Google Sheet yourself using your own account; it has to have the same name as it is shown in the main.py file for "SPREADSHEET_NAME"
7. Click **Share** on that sheet and add the service account's email with **Editor** access; found in the JSON file's `client_email` field


### 3. Configure the script
 
SERVICE_ACCOUNT_FILE = "your-actual-key-filename.json"
SPREADSHEET_NAME = "your_spreadsheet_name"
SERVICE_EMAIL = "your_service_email

change these variables in main.py to fit your needs

You put these in a .env file



## Credits
 
Internship data sourced from SimplifyJobs Summer Internships (https://github.com/SimplifyJobs/Summer2027-Internships) repository.