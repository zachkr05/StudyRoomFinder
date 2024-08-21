import requests
import pprint
import logging
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def getClassesAsJSON():
    """Fetch JSON data from the first 3 pages of a paginated URL or until no more data is available."""
    logging.debug("Starting to fetch class data...")
    sys.stdout.flush()
    base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
    institution = "UVA01"
    term = "1248"
    max_pages = 1000
    page = 1
    all_data = []

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    while page <= max_pages:
        # Construct URL with current page number
        url = f"{base_url}?institution={institution}&term={term}&page={page}"
        logging.debug(f"Fetching data from URL: {url}")
        sys.stdout.flush()
        try:
            response = session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logging.debug(f"Data received for page {page}: {data}")
            sys.stdout.flush()
            # Check if data is an empty list and break if it is
            if not data:
                logging.debug(f"No data found on page {page}. Stopping fetch.")
                sys.stdout.flush()
                break
            all_data.extend(data)
            page += 1  # next page
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred: {e}")
            sys.stdout.flush()
            raise Exception(f"Failed to retrieve data: {e}")

    logging.debug("Finished fetching class data.")
    sys.stdout.flush()
    return all_data

def parseJSON(json_data):
    """Parse specific fields from JSON class data."""
    if not json_data:
        logging.error("No data to parse.")
        sys.stdout.flush()
        raise ValueError("No data to parse.")

    logging.debug("Starting to parse JSON data...")
    sys.stdout.flush()
    class_info_list = []
    # Assuming json_data is a list of class entries
    for class_data in json_data:
        start_date = class_data.get('start_dt', 'No start date provided')
        end_date = class_data.get('end_dt', 'No end date provided')
        description = class_data.get('descr', 'No description provided')
        meeting_details = class_data.get('meetings', [])

        # Format meetings
        formatted_meetings = []
        for meeting in meeting_details:
            formatted_meeting = {
                "Days": meeting.get("days"),
                "Start Time": meeting.get("start_time"),
                "End Time": meeting.get("end_time"),
                "Building Code": meeting.get("bldg_cd"),
                "Room": meeting.get("room"),
                "Facility Description": meeting.get("facility_descr"),
                "Instructor": meeting.get("instructor")
            }
            formatted_meetings.append(formatted_meeting)

        class_info = {
            "Start Date": start_date,
            "End Date": end_date,
            "Description": description,
            "Meetings": formatted_meetings
        }
        class_info_list.append(class_info)

    logging.debug("Finished parsing JSON data.")
    sys.stdout.flush()
    return class_info_list

def organize_by_room(class_data):
    logging.debug("Starting to organize classes by room...")
    sys.stdout.flush()
    room_to_classes = {}
    for class_entry in class_data:
        for meeting in class_entry['Meetings']:
            room_key = f"{meeting['Building Code']} {meeting['Room']}"
            if room_key not in room_to_classes:
                room_to_classes[room_key] = []
            room_to_classes[room_key].append({
                'Start Date': class_entry['Start Date'],
                'End Date': class_entry['End Date'],
                'Description': class_entry['Description'],
                'Meeting Details': meeting
            })
    logging.debug("Finished organizing classes by room.")
    sys.stdout.flush()
    return room_to_classes

# Example usage
try:
    logging.info("Starting the process to fetch and organize class data.")
    sys.stdout.flush()
    json_data = getClassesAsJSON()
    parsed_data = parseJSON(json_data)
    organized_classes = organize_by_room(parsed_data)
    logging.info("Process completed successfully. Here is the organized class data:")
    sys.stdout.flush()
    pprint.pprint(organized_classes)
    sys.stdout.flush()
except Exception as e:
    logging.error(f"An error occurred: {str(e)}")
    sys.stdout.flush()
