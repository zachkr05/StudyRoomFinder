import requests
import pprint
import logging
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.core.management.base import BaseCommand
from classdata.models import ClassInfo, MeetingDetail

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Command(BaseCommand):
    help = 'Fetch class data and store in the database'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting the process to fetch and store class data.", ending='\n')
        json_data = self.get_classes_as_json()
        parsed_data = self.parse_json(json_data)
        self.store_data(parsed_data)
        self.stdout.write("Process completed successfully.", ending='\n')

    def get_classes_as_json(self):
        """Fetch JSON data from the first 3 pages of a paginated URL or until no more data is available."""
        logging.debug("Starting to fetch class data...")
        sys.stdout.flush()
        base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
        institution = "UVA01"
        term = "1248"
        max_pages = 2
        page = 1
        all_data = []


        #for all https requests utilize 3 retries, and a delay of 0.5 seconds in between retries
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)

        #mimic the request of a computer, fixes bug for retries
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        while page <= max_pages:
            # Construct URL with current page number
            url = f"{base_url}?institution={institution}&term={term}&page={page}"
            logging.debug(f"Fetching data from URL: {url}")
            sys.stdout.flush()


            try:

                #logic to fetch data
                response = session.get(url, headers=headers)
                response.raise_for_status() #raise value error
                data = response.json()

                #debug
                logging.debug(f"Data received for page {page}: {data}")
                sys.stdout.flush()

                #logic to check if we reached the end of the class schedule
                # Check if data is an empty list and break if it is
                if not data:
                    logging.debug(f"No data found on page {page}. Stopping fetch.")
                    sys.stdout.flush()
                    break

                all_data.extend(data) # add collected data to list
                page += 1  # next page


            except requests.exceptions.RequestException as e:
                logging.error(f"An error occurred: {e}")
                sys.stdout.flush()
                raise Exception(f"Failed to retrieve data: {e}")

        logging.debug("Finished fetching class data.")
        sys.stdout.flush()
        return all_data

    def parse_json(self, json_data):
        """Parse specific fields from JSON class data."""

        #edge case
        if not json_data:
            logging.error("No data to parse.")
            sys.stdout.flush()
            raise ValueError("No data to parse.")

        logging.debug("Starting to parse JSON data...")
        sys.stdout.flush()
        class_info_list = []

        for class_data in json_data:
            start_date = class_data.get('start_dt', 'No start date provided')
            end_date = class_data.get('end_dt', 'No end date provided')
            description = class_data.get('descr', 'No description provided')
            meeting_details = class_data.get('meetings', [])

            # Format meetings
            formatted_meetings = []
            for meeting in meeting_details:
                #define a dictionary for each class' meeting schuedule
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
            #define a dictionary for each class' class info
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

    def store_data(self, class_data):
        logging.debug("Starting to store data in the database...")
        sys.stdout.flush()

        # Fill out db rows for all entries
        for class_entry in class_data:
            class_info = ClassInfo.objects.create(
                start_date=class_entry['Start Date'],
                end_date=class_entry['End Date'],
                description=class_entry['Description']
            )
            for meeting in class_entry['Meetings']:
                # Safely get 'Building Code' and provide a default value if None or missing
                building_code = meeting.get('Building Code')
                if building_code is None:
                    building_code = "N/A"

                # Safely get 'Room' and provide a default value if None or missing
                room = meeting.get('Room')
                if room is None:
                    room = "N/A"

                # Safely get 'Facility Description' and provide a default value if None or missing
                facility_description = meeting.get('Facility Description')
                if facility_description is None:
                    facility_description = "No Description"

                # Safely get 'Instructor' and provide a default value if None or missing
                instructor = meeting.get('Instructor')
                if instructor is None:
                    instructor = "TBA"

                # Create the MeetingDetail object with default values where necessary
                MeetingDetail.objects.create(
                    class_info=class_info,
                    days=meeting['Days'],
                    start_time=meeting['Start Time'],
                    end_time=meeting['End Time'],
                    building_code=building_code,
                    room=room,
                    facility_description=facility_description,
                    instructor=instructor
                )

        logging.debug("Finished storing data in the database.")
        sys.stdout.flush()

