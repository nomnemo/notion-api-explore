import os 
import requests
import pandas as pd
from notion_client import Client as NotionClient

# we got the api token
auth_token = "secret_a3gznPNkLmhgiOpciAWMjIEtpINpp5h9sKOhP7Nu05X"

# The page ID you want to retrieve
database_id = 'f0882a36a9d340b3a9ff7e20ee2441d7'

# Set up the URL and headers
url = f'https://api.notion.com/v1/databases/{database_id}/query'

headers = {
    'Authorization': f'Bearer {auth_token}',
    'Notion-Version': '2022-06-28'  # Use the latest version supported by the API
}
# Perform the POST request, TODO: Why not GET request instead ?
response = requests.post(url, headers=headers)

# Check the response in prettier form:
if response.status_code == 200:
    print("Database data retrieved successfully!")
    data = response.json()
    
    # Parsing the data
    results = data.get('results', [])
    parsed_data = []
    for result in results:
        properties = result.get('properties', {})
        entry = {
            'Company Name': properties.get('Company name', {}).get('title', [{}])[0].get('text', {}).get('content', ''),
            'Application Status': properties.get('application', {}).get('status', {}).get('name', ''),
            'CoA': properties.get('CoA', {}).get('status', {}).get('name', ''),
            'Interview Status': properties.get('Interview', {}).get('status', {}).get('name', ''),
            'Location': properties.get('Location', {}).get('multi_select', [{}])[0].get('name', ''),
            'LinkedIn Connection': properties.get('Linkedin Connection', {}).get('checkbox', False)
        }
        parsed_data.append(entry)
    
    print(parsed_data)
    # Displaying data in a tabular format using pandas
    df = pd.DataFrame(parsed_data)
    print(df)
else:
    print("Failed to retrieve database")
    print(response.text)  # This will print any error messages
    
