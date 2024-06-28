import os
import requests
import pandas as pd
import sqlite3  # Ensure sqlite3 is imported
from sqlalchemy import create_engine
from notion_client import Client as NotionClient

# Greetings
print("\nHi, welcome. \n\nLet's add some new internships to apply to your Notion recruiting management database!\n")
print("I will guide you with the steps to do so. Bear with me and follow along!\n")
print("1. Download the job posting CSV file from GitHub page: https://github.com/public-apis/public-apis?tab=readme-ov-file \n")
print("2. Import the Job Posting .csv file into the same folder!\n")
initial_step = input("Press Enter when you are done:")

csv_file_path = input("Please enter the name of your CSV file:\n")

# Show the user that their file is being searched
print("\n...searching...\n")

# Check if the file exists
if not os.path.isfile(csv_file_path):
    print("\nFile not found. Please place the CSV file in the same folder or provide the absolute path.\n")
else:
    print(" > File successfully found!")

    # Load CSV data into a DataFrame
    df = pd.read_csv(csv_file_path)
    print(" > DataFrame successfully created!")

    # Ensure the dates are in the correct format
    df['Open Date'] = pd.to_datetime(df['Open Date']).dt.strftime('%Y-%m-%d')
    df['Deadline date'] = pd.to_datetime(df['Deadline date']).dt.strftime('%Y-%m-%d')

    # Extract unique locations
    all_locations = df['Location(s)'].str.split(',').explode().str.strip().unique()
    filtered_locations = [location for location in all_locations if len(location) != 2]

    print("\nUnique locations found in the CSV file are:")
    for location in filtered_locations:
        print(location)

    # Connect to the database using SQLite3
    sqlite_db_path = "name"
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()

    # Create a table in the SQLite database
    table_name = 'internship_postings'
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    print(f"\nData from {csv_file_path} has been successfully imported into {sqlite_db_path} as table '{table_name}'.\n")

    # Fetch the first few records
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
    rows = cursor.fetchall()

    # Display the records
    print(f"\nSee the first few records of the table '{table_name}':\n")
    for row in rows:
        print(row)

    # Close the connection after fetching the initial records
    conn.close()

    # Reconnect to the database to query internships based on user input
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()

    # Ask for the location and date for querying the internships
    location_input = input("Please enter the location: ")
    date = input("Please enter the date (YYYY-MM-DD): ")

    # Ensure the input date is in the correct format
    date = pd.to_datetime(date).strftime('%Y-%m-%d')

    # Split the location input into a list of locations
    locations = [loc.strip() for loc in location_input.replace(',', ' ').split()]

    # Construct the SQL query with multiple LIKE conditions
    location_conditions = " OR ".join([f'"Location(s)" LIKE \'%{loc}%\'' for loc in locations])
    query = f"""
    SELECT * FROM {table_name}
    WHERE ({location_conditions}) AND "Open Date" <= '{date}' AND "Deadline date" >= '{date}'
    ORDER BY "Open Date" DESC
    """
    result_df = pd.read_sql(query, conn)

    # Display the matching internships
    print("\nMatching internships:")
    print(result_df[['Title', 'Company', 'Open Date', 'Deadline date']])

    # Ask if the user wants to add these internships to their Notion database
    add_to_notion = input("\nDo you want to add these internships to your Notion database? (yes/no): ")

    if add_to_notion.lower() == 'yes':
        # Get the Notion integration token and database ID from the user
        auth_token = input("Please enter your Notion integration token: ")
        notion = NotionClient(auth=auth_token)
        database_id = input("Please enter your Notion database ID: ")

        # Function to add a job application to Notion
        def add_job_application(title, company, deadline_date, location):
            url = 'https://api.notion.com/v1/pages'
            data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    },
                    "Company": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": company
                                }
                            }
                        ]
                    },
                    "Deadline Date": {
                        "date": {
                            "start": deadline_date
                        }
                    },
                    "Location": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": location
                                }
                            }
                        ]
                    },
                }
            }

            response = requests.post(url, headers={
                'Authorization': f'Bearer {auth_token}',
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }, json=data)
            return response

        # Add each matching internship to Notion
        for index, row in result_df.iterrows():
            response = add_job_application(row['Title'], row['Company'], row['Deadline date'], row['Location(s)'])
            if response.status_code == 200:
                print(f"Successfully added: {row['Title']} at {row['Company']}")
            else:
                print(f"Failed to add: {row['Title']} at {row['Company']}. Error: {response.json()}")

    # Close the connection
    conn.close()
