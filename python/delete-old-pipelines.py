#!/usr/bin/env python3
#################################################################
# FILE:  delete-old-pipelines.py
#
# DESCRIPTION:    This script attempts to delete pipelines listed in the input file.
#
# ARGS:           - input_file - A JSON list of pipelines to delete.
#
# USAGE:          $ python3 delete-old-pipelines.py <input_file>
#
# USAGE EXAMPLE:  $ python3 delete-old-jpipelines.py /Users/mark/old-pipelines/old_pipelines.json
#
# PREREQUISITES:
#
#  - Python 3.9+
#
# - StreamSets Platform SDK for Python v6.0+
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

import os,sys, json
from pathlib import Path
from datetime import datetime
from streamsets.sdk import ControlHub

# Method that validates the input_file command line parameter.
# Returns True if the input_file exists and is readable or False otherwise
def validate_input_file_parameter(the_input_file):
    file_path = Path(the_input_file)
    if file_path.is_file() and os.access(file_path, os.R_OK):
        return True
    else:
        print(f"Error: Input File \'{input_file}\' either does not exist or is not readable")
        return False

# Method to get a pipeline from SCH using the pipeline_id. Returns the pipeline or None if the
# pipeline is not found or if there is any issue
def get_pipeline(the_pipeline_info):
    pipeline_id = the_pipeline_info["pipeline_id"]
    pipeline_name = the_pipeline_info["pipeline_name"]

    try:
        query = 'pipeline_id=="' + pipeline_id + '"'
        pipelines = sch.pipelines.get_all(search=query)
        if pipelines is None or len(pipelines) == 0:
            print(f"Error getting pipeline \'{pipeline_name}\': Pipeline not found")
        else:
            pipeline = pipelines[0]
            return pipeline
    except Exception as ex:
        print(f"Error getting pipeline \'{pipeline_name}\': {ex}")
    return None

# Method to delete a pipeline. The deletion attempt might fail due to permission issues
# or if the pipeline is associated with a Job
def delete_pipeline(pipeline):
    try:
        sch.delete_pipeline(pipeline)
        print('- Pipeline was deleted.')
    except Exception as ex:
        print(f"Error: Attempt to delete pipeline \'{pipeline_name}\' with ID \'{pipeline_id}\' failed; {ex}")

# Method to handle each line of the input file
def handle_line(the_pipeline_info):

    print(f"Preparing to delete pipeline \'{the_pipeline_info['pipeline_name']}\' with ID \'{the_pipeline_info['pipeline_id']}\'")

    # Get the pipeline
    pipeline = get_pipeline(the_pipeline_info)
    if pipeline is not None:

        print("- Found Pipeline")

        # Try to delete the pipeline
        delete_pipeline(pipeline)

    print("---------------------------------")

#####################################
# Main Program
#####################################

# Get CRED_ID from the environment
CRED_ID = os.getenv('CRED_ID')

# Get CRED_TOKEN from the environment
CRED_TOKEN = os.getenv('CRED_TOKEN')

# Check the number of command line args
if len(sys.argv) != 2:
    print('Error: Wrong number of arguments')
    print('Usage: $ python3 delete-old-pipelines.py <input_file>')
    print('Usage Example: $ python3 delete-old-pipelines /Users/mark/old-jobs/old_jobs.json')
    sys.exit(1)

# Validate the input_file parameter
input_file = sys.argv[1]
print("---------------------------------")
print(f"input_file: '{input_file}'")
if not validate_input_file_parameter(input_file):
    sys.exit(1)

# Connect to Control Hub
print("---------------------------------")
print('Connecting to Control Hub')
print("---------------------------------")
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)

# Process each line of the input_file
with open(input_file, 'r') as f:
    for line in f:
        try:
            pipeline_info = json.loads(line)
            handle_line(pipeline_info)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON for line {line}: {e}")

print('Done')
