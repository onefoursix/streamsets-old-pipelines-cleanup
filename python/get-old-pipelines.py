#!/usr/bin/env python3
#################################################################
# FILE:  get-old-pipelines.py
#
# DESCRIPTION:    This script writes a list of pipelines that are not associated with any Jobs and that
#                 have not been modified since before a user-defined last_modification_date_threshold parameter
#
# ARGS:           - last_modification_date_threshold     - A String in the form yyyy-mm-dd
#
#                 - output_file        - The full path to a file where the list of old pipelines will be written.
#                                        Directories in the path will be created as needed, and if an existing
#                                        file of the same name exists, it will be overwritten.
#
# USAGE:          $ python3 get-old-pipelines.py <last_modification_date_threshold> <output_file>
#
# USAGE EXAMPLE:  $ $ python3 get-old-pipelines.py 2024-06-30 /Users/mark/old-pipelines/old_pipelines.json
#
# PREREQUISITES:
#
#  - Python 3.9+
#
# - StreamSets Platform SDK for Python v6.6+
#   See: https://docs.streamsets.com/platform-sdk/latest/welcome/installation.html
#
# - StreamSets Platform API Credentials for a user with Organization Administrator role
#
# - Before running the script, export the environment variables CRED_ID and CRED_TOKEN
#  with the StreamSets Platform API Credentials, like this:
#
#    $ export CRED_ID="40af8..."
#    $ export CRED_TOKEN="eyJ0..."
#
#################################################################

import os,sys,json
from pathlib import Path
from datetime import date, datetime, timedelta
from streamsets.sdk import ControlHub

# Method to convert millis to datetime string
def millis_to_datetime_string(millis):
    seconds = millis / 1000.0
    dt = datetime.fromtimestamp(seconds)
    dt_string = dt.strftime('%Y-%m-%d %H:%M:%S')
    return dt_string

# Method to convert datetime string to millis
def convert_datetime_string_to_millis(datetime_string):
    try:
        dt = datetime.strptime(datetime_string, "%Y-%m-%d")
        millis = int(dt.timestamp() * 1000)
        return millis
    except Exception as e:
        print(f"Error: Error converting \'{datetime_string}\' to millis: \'{e}\'.")
    return None

# Method that validates the last_modification_date_threshold parameter is a valid date
def is_valid_date(the_date_str):
    try:
        # This line will throw an exception if the date string is not valid
        datetime.strptime(the_date_str, "%Y-%m-%d")
        return True
    except ValueError:
        print(f"Error: The last_modification_date_threshold parameter \'{the_date_str}\' is not a valid date in yyyy-mm-dd format.")
    return False

# Method that validates that the last_modification_date_threshold parameter is at
# least one day behind the current date.
def date_is_at_least_one_day_old(the_date_str):
    the_date = datetime.strptime(the_date_str, "%Y-%m-%d")
    if the_date.date() <= date.today() - timedelta(days=1):
        return True
    else:
        print(f"Error: The last_modification_date_threshold parameter \'{the_date_str}\' is not at least one day earlier than the current date.")
    return False

# Method that validates the output file and creates the directories in the path if necessary.
# Returns True if the output file and path are valid or False if not.
def validate_output_file_parameter(the_output_file):

    # Get output file's path
    path = Path(the_output_file)

    # Try to create parent folder if it does not already exist
    parent_dir = path.parent
    if parent_dir.is_dir():
        return True
    else:
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory \'{parent_dir}\'")
            return True
        except PermissionError:
            print(f"Error: Permission denied when trying to create directory \'{parent_dir}\'")
            return False
        except OSError as e:
            print(f"Error: OS error when trying to create directory \'{parent_dir}\': {e}")
            return False

# Method that returns True if any version of the pipeline is associated with a Job or False otherwise
def is_pipeline_associated_with_a_job(the_pipeline):
    # Loop through every version of the pipeline
    for commit in the_pipeline.commits:
        if commit.commit_id in pipelines_used_in_jobs:
            return True
    return False

#####################################
# Main Program
#####################################

# Get CRED_ID from the environment
CRED_ID = os.getenv('CRED_ID')

# Get CRED_TOKEN from the environment
CRED_TOKEN = os.getenv('CRED_TOKEN')

# A list of old pipelines not associated with Jobs
old_pipelines = []

# Check the number of command line args
if len(sys.argv) != 3:
    print('Error: Wrong number of arguments')
    print('Usage: $ python3 get-old-pipelines.py <last_modification_date_threshold> <output_file>')
    print('Usage Example: $ python3 get-old-pipelines.py 2024-06-30 /Users/mark/old-pipelines/old_pipelines.json')
    sys.exit(1)

# Validate the last_modification_date_threshold parameter
last_modification_date_threshold = sys.argv[1]
last_modification_date_threshold_millis = None
if is_valid_date(last_modification_date_threshold) and date_is_at_least_one_day_old(last_modification_date_threshold):
    last_modification_date_threshold_millis = convert_datetime_string_to_millis(last_modification_date_threshold)
if last_modification_date_threshold is None:
    sys.exit(1)

# Validate the output_file parameter
output_file = sys.argv[2]
if not validate_output_file_parameter(output_file):
    sys.exit(1)

print("---------------------------------")
print('Searching for old pipelines not associated with Jobs')
print(f"Last Modification Date Threshold: '{last_modification_date_threshold}'")
print(f"Output file: '{output_file}'")

# Connect to Control Hub
print("---------------------------------")
print('Connecting to Control Hub')
print("---------------------------------")
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)

# Store which pipelines are used by Jobs
pipelines_used_in_jobs = []

# Get pipelines associated with Jobs
print('Getting Job/Pipeline associations')
print("---------------------------------")
for job in sch.jobs:
    pipelines_used_in_jobs.append(job.commit_id)

# Look for old pipelines
print('Searching for old pipelines not associated with Jobs.')
print('Please be patient; this may take a while...')
print('...')

# Loop through every pipeline
for pipeline in sch.pipelines:

    # If the pipeline is not associated with a Job
    if not is_pipeline_associated_with_a_job(pipeline):

        # See if the pipeline's last modification is before the threshold
        if pipeline.last_modified_on < last_modification_date_threshold_millis:

            last_modified_date = millis_to_datetime_string(pipeline.last_modified_on)

            # Add the pipeline id to the list of old pipelines
            old_pipelines.append({'pipeline_name': pipeline.name,
                                  'pipeline_id': pipeline.pipeline_id,
                                  'last_modified': last_modified_date})

print("---------------------------------")
    # Write the old pipelines to the output file in alphabetical order
    # This will overwrite a pre-existing file of the same name


if len(old_pipelines) > 0:
    print('Writing the list of old pipelines to the output file')
    old_pipelines_sorted = sorted(old_pipelines, key=lambda x: x['pipeline_name'])
    # Write to JSON file
    with open(output_file, 'w') as f:
        json.dump(old_pipelines_sorted, f, indent=2)
    print(f'Found {len(old_pipelines)} old pipelines not associated with any Jobs.')
else:
    print("No old pipelines not associated with Jobs were found.")

print("---------------------------------")
print('Done')
