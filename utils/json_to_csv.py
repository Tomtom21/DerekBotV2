import json
import csv


def json_to_csv(json_file, csv_file):
    # Load the JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Ensure data is a list of dictionaries
    if not isinstance(data, list):
        raise ValueError("JSON data must be a list of dictionaries.")

    # Extract headers from keys of the first dictionary
    headers = data[0].keys()

    # Write CSV file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)


# Example usage
json_to_csv('birthdays.json', 'output.csv')
