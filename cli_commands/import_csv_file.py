"""
Imports a CSV file into the database.
Retrieved from instagram scraper of public emails.

Other formats can be supported by modifying the code below.
"""
import csv

from tqdm import tqdm

from bot.services.email_validator import EmailValidator
from bot.webapp.models import Contact


def scan_and_parse_csv_files(folder_location):
    """
    Scans a folder for CSV files and returns a list of the files.
    :param folder_location:
    :return:
    """
    import os
    import glob

    user_details = []

    csv_files = glob.glob(os.path.join(folder_location, "*.csv"))
    total_contacts_prior = Contact.query.count()
    print(f"Found {len(csv_files)} CSV files in {folder_location}.")
    for file in csv_files:
        print(f"~ Beginning Extraction of: {file}")
        user_details += import_csv_file_command(csv_file_location=file, silent=True)

    contacts_after = Contact.query.count()
    print(f"Added {contacts_after - total_contacts_prior} contacts to the database.")
    return user_details


def import_csv_file_command(csv_file_location, silent=False):
    user_details = []  # List of dictionaries containing user details
    duplicate_user = 0
    _raw_details = []

    with open(csv_file_location, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        lines = 0
        for line in csv_reader:
            if lines == 0:
                lines += 1
                continue
            try:
                user_info = dict(
                    username=line[1],
                    full_name=line[2],
                    email=line[6],
                    bio=line[14],
                    instagram_url=line[16],
                    business="y" in line[12].lower()
                )
            except:
                print(f"Error parsing line {lines} in {csv_file_location} - Invalid format.")
                continue  # Invalid Format
            _raw_details.append(user_info)

    user_pbar = tqdm(_raw_details, desc=f"Processing {len(_raw_details)} users from CSV file import...",
                     total=len(_raw_details))
    for user_info in user_pbar:

        user_pbar.set_description(f"Processing {user_info['email']}")

        contact = Contact.query.filter_by(email=user_info['email']).first()
        if contact is not None:
            duplicate_user += 1 # todo implement check for recently emailed users right here.
            user_pbar.set_description(f"Skipping {user_info['email']} (duplicate email)")
            continue
        # Fail first logic. Less queries could be better.
        contact = Contact(full_name=user_info["full_name"], instagram_url=user_info["instagram_url"],
                          email=user_info["email"], bio=user_info["bio"], business=user_info['business'],
                          verified_email=False)
        contact.save(commit=True)

        user_info['contact'] = contact

        user_details.append(user_info)
        lines += 1
        user_pbar.set_description(f"+ {user_info['email']}")

    if not silent:
        print(
            f"Parsed file to find {len(user_details)} users.\nDuplicate Information of {duplicate_user} users already exists in the database.\n + {len(user_details)} users added to the database.")
    return user_details
