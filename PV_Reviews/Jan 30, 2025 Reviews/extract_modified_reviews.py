import json
import csv
from datetime import datetime, timedelta

# Load the JSON data from the file
with open('/Users/rajeshpanchanathan/Documents/PythonWork/PV_Reviews/Jan 30, 2025 Reviews/combined.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# List to store the extracted records
extracted_records = []

# Function to calculate the time difference in hours
def time_difference_hours(create_time, update_time):
    create_datetime = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
    update_datetime = datetime.fromisoformat(update_time.replace('Z', '+00:00'))
    return (update_datetime - create_datetime).total_seconds() / 3600  # Convert to hours

# Iterate through the JSON data
for entry in data:
    for review in entry['reviews']:
        # Calculate the time difference in hours
        time_diff_hours = time_difference_hours(review['createTime'], review['updateTime'])
        
        # Check if the difference is more than 24 hours
        if time_diff_hours > 24:
            # Prepare the record data
            record = {
                'reviewer': review['reviewer']['displayName'],
                'starRating': review['starRating'],
                'comment': review.get('comment', ''),  # Some reviews may not have a comment
                'createTime': review['createTime'],
                'updateTime': review['updateTime'],
                'timeDifference_hours': time_diff_hours,  # Add the time difference in hours
                'reviewReply_comment': review.get('reviewReply', {}).get('comment', ''),  # Some reviews may not have a reply
                'reviewReply_updateTime': review.get('reviewReply', {}).get('updateTime', '')  # Some reviews may not have a reply
            }
            # Add the record to the list
            extracted_records.append(record)

# Write the extracted records to a CSV file
csv_file = '/Users/rajeshpanchanathan/Documents/PythonWork/PV_Reviews/Jan 30, 2025 Reviews/extracted_records_24hrs.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=extracted_records[0].keys())
    writer.writeheader()
    writer.writerows(extracted_records)

print(f"Extracted {len(extracted_records)} records and saved to {csv_file}")