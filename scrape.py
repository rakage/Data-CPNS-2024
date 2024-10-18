import requests
import json
import pandas as pd
from openpyxl import load_workbook
import os
from requests.exceptions import RequestException
import time
import re

# Load data from JSON files
with open('data2.json') as f:
    data_list = json.load(f)

with open('data_instansi.json') as f:
    data_instansi_list = json.load(f)

# Define the headers
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Host': 'api-sscasn.bkn.go.id',
    'Origin': 'https://sscasn.bkn.go.id',
    'Referer': 'https://sscasn.bkn.go.id/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}

# Define the base URL
url = "https://api-sscasn.bkn.go.id/2024/portal/spf"

def make_request_with_retry(url, headers, params, max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response
        except RequestException as e:
            print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Giving up.")
                raise

def sanitize_filename(filename):
    # Replace slashes with underscores and remove any other invalid characters
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

# Iterate over each item in the data lists
for data_json in data_list:
    for data_instansi_json in data_instansi_list:
        # Extract cepat_kode for kode_ref_pend
        kode_ref_pend = data_json.get('cepat_kode')

        # Extract id for instansi_id
        instansi_id = data_instansi_json.get('id')

        # Define query parameters
        params = {
            'kode_ref_pend': kode_ref_pend,
            'instansi_id': instansi_id,
            'limit': '10',
            'offset': '0'
        }

        # Initialize list to hold all data
        all_data = []

        # Initialize variables
        offset = 0
        limit = 10

        while True:
            params['offset'] = str(offset)

            try:
                # Make the GET request with retry
                response = make_request_with_retry(url, headers, params)

                data = response.json()

                # Access the 'data' key in the response
                data_meta = data.get('data')
                if not data_meta:
                    print(f"No 'data' key found in response: {data}")
                    break

                # Access the actual data records
                page_data = data_meta.get('data', [])

                # Debugging: print the fetched page data
                print(f"Fetched data (offset {offset}):", page_data)

                # Check if page_data is a list and not empty
                if isinstance(page_data, list) and page_data:
                    all_data.extend(page_data)

                    # Access 'page' information if it exists
                    page_info = data_meta.get('page', {})
                    total_pages = page_info.get('total', 1)
                    current_page = (offset // limit) + 1

                    if current_page >= total_pages:
                        break

                    # Update offset for the next page
                    offset += limit
                else:
                    print("No data found or unexpected data structure.")
                    break

            except Exception as e:
                print(f"Error: {e}")
                break

        # Save the fetched data to an Excel file based on the 'nama' field from data.json
        if all_data:
            # Convert the list of dictionaries to a DataFrame
            df = pd.DataFrame(all_data)

            # Generate the output filename
            sanitized_name = sanitize_filename(data_json.get('nama', 'unnamed'))
            output_filename = f"{sanitized_name}_data.xlsx"

            if os.path.exists(output_filename):
                # If the file exists, load it and append the new data
                with pd.ExcelWriter(output_filename, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1', startrow=writer.sheets['Sheet1'].max_row, header=False)
            else:
                # If the file does not exist, create it
                df.to_excel(output_filename, index=False, sheet_name='Sheet1')

            print(f"Data appended to {output_filename}")
        else:
            print(f"No data found for {data_json.get('nama')}")
