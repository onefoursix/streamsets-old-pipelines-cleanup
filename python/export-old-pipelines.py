#!/usr/bin/env python3
#################################################################
# FILE:  export-old-pipelines.py
#
# DESCRIPTION:    This script exports the current version of the pipelines listed in the input file.
#
# ARGS:           - input_file - A JSON list of pipelines to export.
#
#                 - export_dir - The directory to write the exported pipelines to.
#                                The directory will be created if it does not exist.
#                                If the directory does exist, it must be empty
#
# USAGE:          $ python3 export-old-pipelines.py <input_file> <export_dir>
#
# USAGE EXAMPLE:  $ python3 export-old-pipelines.py /Users/mark/old-pipelines/old_pipelines.json /Users/mark/pipelines-export
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
from streamsets.sdk import ControlHub

# Method that validates the input_file command line parameter.
# Returns True if the input_file exists and is readable or False otherwise
def validate_input_file_parameter(the_input_file):
    file_path = Path(the_input_file)
    if file_path.is_file() and os.access(file_path, os.R_OK):
        return True
    else:
        print(f"Error: Input File \'{the_input_file}\' either does not exist or is not readable")
        return False

# Method that validates that the directory specified in the export_dir command line parameter either
# does not exist or exists but is an empty dir. If the directory does not exist it will be created.
# Returns True if the directory is OK or False if not.
def validate_export_dir_parameter(the_export_dir):

    # If export_dir already exists...
    if os.path.isdir(the_export_dir):
        # ... make sure it is empty
        if os.listdir(the_export_dir):
            print(f"Error: Export directory \'{the_export_dir}\' already exists but is not empty. ")
            print("Please specify a new or empty directory for Job export")
            return False

    # Create export dir if it does not yet exist
    else:
        try:
            os.makedirs(the_export_dir, exist_ok=True)
            if not os.path.isdir(the_export_dir):
                print("Error: directory creation failed.")
                return False
        except Exception as ex:
            print(f"Exception when trying to create directory \'{the_export_dir}\': {ex}")
            return False
    return True

#####################################
# Main Program
#####################################

# Get CRED_ID from the environment
CRED_ID = os.getenv('CRED_ID')

# Get CRED_TOKEN from the environment
CRED_TOKEN = os.getenv('CRED_TOKEN')

# Check the number of command line args
if len(sys.argv) != 3:
    print('Error: Wrong number of arguments')
    print('Usage: $ python3 export-old-pipelines.py <input_file> <export_dir>')
    print('Usage Example: $ python3 export-old-pipelines.py /Users/mark/old-pipelines/old_pipelines.json /Users/mark/pipelines-export')
    sys.exit(1)

# Validate the input_file parameter
input_file = sys.argv[1]
print("---------------------------------")
print(f"input_file: '{input_file}'")
if not validate_input_file_parameter(input_file):
    sys.exit(1)

# Validate the export_dir parameter
export_dir = sys.argv[2]
print("---------------------------------")
print(f"export_dir: '{export_dir}'")
if not validate_export_dir_parameter(export_dir):
    sys.exit(1)

# Connect to Control Hub
print("---------------------------------")
print('Connecting to Control Hub')
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)

print("---------------------------------")
print('Exporting Pipelines...')
print("---------------------------------")

# Process each line of the input_file
with open(input_file, 'r') as f:
    for line in f:
        try:
            obj = json.loads(line)
            pipeline_id = obj["pipeline_id"]

            try:
                # Get the pipeline from Control Hub using its ID
                query = 'pipeline_id=="' + pipeline_id + '"'
                pipelines = sch.pipelines.get_all(search=query)

                # Handle if pipeline is not found
                if pipelines is None or len(pipelines) == 0:
                    print(f"Error exporting pipeline \'{obj["pipeline_name"]}\' with pipeline ID \'{pipeline_id}\': Pipeline not found")

               # Export Pipeline
                else:
                    pipeline = pipelines[0]
                    got_pipeline = True

                    # If the pipeline is a draft version, get the last published version instead
                    if pipeline.draft:
                        print(f"Pipeline \'{obj["pipeline_name"]}\' version \'{pipeline.version}\' with pipeline ID \'{pipeline_id}\' is a draft pipeline and can't be exported.")
                        print("Looking for the most recent published version of the pipeline...")

                        # See if a version of the pipeline has been published
                        commits = pipeline.commits
                        if commits is None or len(commits) == 0:
                            print("No published versions found for this pipeline")
                            print(f"Warning: Pipeline \'{obj["pipeline_name"]}\' with pipeline ID \'{pipeline_id}\' was not exported!")
                            got_pipeline = False

                        else:
                            # Get the most recent published version
                            most_recent_commit = max(commits, key=lambda c: c.commit_time)
                            # Get the most recent commit of the pipeline from Control Hub using its ID
                            query = 'pipeline_id=="' + pipeline_id + '" and version=="' +  most_recent_commit.version + '"'
                            pipelines = sch.pipelines.get_all(search=query)

                            if pipelines is None or len(pipelines) == 0:
                                print("Error: Unable to retrieve a published version of this pipeline")
                                got_pipeline = False

                            else:
                                pipeline = pipelines[0]
                                print(f"Found version \'{pipeline.version}\' of the pipeline")
                                got_pipeline = True

                    if got_pipeline:
                        # replace '/' with '_' in pipeline name
                        pipeline_name = pipeline.name.replace("/", "_")
                        export_file_name = export_dir + '/' + pipeline_name + '.zip'

                        print(f"Exporting pipeline \'{pipeline.name}\' version \'{pipeline.version}\' with pipeline ID \'{pipeline.pipeline_id}\'into the file \'{export_file_name}\'")

                        data = sch.export_pipelines([pipeline], fragments=True, include_plain_text_credentials=False)

                        # Write a zip file for the Job
                        with open(export_file_name, 'wb') as file:
                            file.write(data)

            except Exception as e:
                print(f"Error exporting pipeline \'{pipeline.name}\': {e}")

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON for line {line}: {e}")

        print("---------------------------------")

print('Done')
