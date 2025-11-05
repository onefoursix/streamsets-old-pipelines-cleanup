# streamsets-old-pipelines-cleanup

This project provides three utility scripts that use the [IBM StreamSets SDK for Python](https://support-streamsets-com.s3.us-west-2.amazonaws.com/streamsets-docs/platform-sdk/latest/index.html) to clean up old pipelines from [IBM StreamSets](https://www.ibm.com/products/streamsets).  Pipelines are considered old if no version of the pipeline is associated with a Job and the last modification to the pipeline was before a user-specified "last modified date threshold". 

The scripts perform the following actions and are intended to be run in the following order to minimize risk when deleting pipelines:

- Script #1 [get-old-pipelines.py](python/get-old-pipelines.py): This script writes a list of pipelines that meet two criteria:  no version of the pipeline is associated with a Job and the last modification to the pipeline was before a user-specified "last modified date threshold".  

- Script #2 [export-old-pipelines.py](python/export-old-pipelines.py): This script exports the most current non-DRAFT version of each pipeline in the list created by script #1. The exports serve as backups in case any pipelines deleted by script #3 need to be restored.  Please carefully read the "Important Note" in the details below regarding the handling of pipeline DRAFT versions.  **TL;DR -- Publish any DRAFT versions you want to export!**

- Script #3 [delete-old-pipelines.py](python/delete-old-pipelines.py): This script deletes the pipelines in the list created by script #1. The script will write a list of pipelines that were successfully deleted and those that were not. The API credentials used to run this script must have at least read/write permissions on the pipelines in order to delete them. 

***
Note that all three of these scripts could relatively easily be clubbed together into a single script, and one could add a "dry run" feature, but I chose to use three separate scripts so the critical "delete pipeline" logic (in script #3) could more easily be inspected for correctness.  Additionally, this approach allows the user to edit the list of old pipelines created by the first script to control which pipelines will be deleted by the third script.

***

See the details for running each script below.

## Prerequisites

- Python 3.9+

- StreamSets Platform SDK for Python v6.6+. Docs are [here](https://docs.streamsets.com/platform-sdk/latest/welcome/installation.html)

 - StreamSets Platform API Credentials for a user with at least read/write permissions for the pipelines to be deleted.

 - Before running any of the scripts, export the environment variables <code>CRED_ID</code> and <code>CRED_TOKEN</code>
  with StreamSets Platform API Credentials, like this:
```
    	$ export CRED_ID="40af8..."
    	$ export CRED_TOKEN="eyJ0..."
```

## Script #1 - get-old-pipelines.py

Description:   This script writes a list of old pipelines.   Pipelines are considered old if no version of the pipeline is associated with a Job and the last modification to the pipeline was before a user-specified "last modified date threshold". 

#### Args:

- <code>last_modification_date_threshold</code> - A String in the form yyyy-mm-dd that is the threshold date to mark pipelines as needing to be cleaned up if they have not been modified since before that date, and if no version of the pipeline is associated with a Job.

- <code>output_file</code> - The full path to a file where the list of old pipelines will be written. Directories in the path will be created as needed, and if an existing file of the same name exists, it will be overwritten.



#### Usage:          
<code>$ python3 get-old-pipelines.py <last_modification_date_threshold> <output_file></code>

#### Usage Example:   
<code>$ python3 get-old-pipelines.py 2023-10-12 /Users/mark/old-pipelines/old_pipelines.json</code>

#### Example Run:
```
$ python3get-old-pipelines.py 2023-10-12 /Users/mark/old-pipelines/old_pipelines.json 

---------------------------------
Searching for old pipelines not associated with Jobs
Last Modification Date Threshold: '2023-10-12'
Output file: '/Users/mark/old-pipelines/old_pipelines.json'
---------------------------------
Connecting to Control Hub
---------------------------------
Getting Job/Pipeline associations
---------------------------------
Searching for old pipelines not associated with Jobs.
Please be patient; this may take a while...
...
---------------------------------
Found 190 old pipelines not associated with any Jobs.
Writing the list of old pipelines to the output file.
---------------------------------
Done


```
Here is a snippet of the data written to the output file <code>old_pipelines.json</code> including the pipeline name, id, last modified timestamp, version number and if the pipeline is a Draft version or not. Note that the pipelines are sorted in alphabetical order by name:

```
{"pipeline_name": "Convert_JSON_to_CSV", "pipeline_id": "a8e68710-5bec-4e69-aad3-8d11553d52ca:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_modified": "2023-10-07 21:15:14", "version": "6", "is_draft": false}
{"pipeline_name": "Create Data for Use Case 3", "pipeline_id": "72a2be2d-fb81-48a7-846a-1d1e25bec4ca:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_modified": "2023-10-06 15:53:01", "version": "1-DRAFT", "is_draft": true}
{"pipeline_name": "Create Trips Facts", "pipeline_id": "a86adf84-cd6f-4aa2-949e-cc2cdf5895f0:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_modified": "2023-09-27 13:07:03", "version": "18.5-DRAFT", "is_draft": true}


```

## Script #2 - export-old-pipelines.py

Description:   This script exports the latest non-Draft version of each pipeline listed in the input file. The exports serve as backups in case any pipelines deleted by script #3 need to be restored. 

<hr>

**Important Note:** In order to avoid the chance of exporting any plain-text credentials, this script sets <code>include_plain_text_credentials</code> to <code>False</code> in the <code>sch.export_pipelines</code> command. 

***This has the side effect of not allowing Draft versions of pipelines to be exported.***
Please contact me at <code>mark.brooks@ibm.com</code> if you want to change this behavior.  

The current version of this script will handle Draft versions of pipelines in the following manner:

- If the latest modified version of a pipeline is <code>V1-DRAFT</code>, the pipeline will not be exported as there are no published versions!

- If the latest modified version of a pipeline is a <code>DRAFT</code> version higher than <code>V1</code> (i.e at least one version of the pipeline was published), the pipeline will export the version with the most recent "last modified" timestamp, which may not necessarily be the highest version number. For example, if v3.3 was published more recently than v5, v3.3 will be exported.

This script could be modified to export every version of every pipeline but that struck me as excessive.  Once again, let me know if you want to change the default behavior of this script.

See the output messages below for example of handling these scenarios.
<hr>

#### Args:

- <code>input_file</code> - A JSON list of pipelines to export (i.e. the output file written by script #1)

- <code>export_dir</code> - The directory to write the exported pipelines to. The directory will be created if it does not exist. If the directory does exist, it must be empty

#### Usage:          
<code>$ python3 export-old-pipelines.py <input_file> <export_dir></code> 

#### Usage Example:  
<code>$ python3 export-old-pipelines.py /Users/mark/old-pipelines/old_pipelines.json /Users/mark/pipelines-export</code>

This script does not write a log, so if you want to capture the results of this script in a file, redirect its output like this:

<code>$ python3 export-old-pipelines.py /Users/mark/old-pipelines/old_pipelines.json /Users/mark/pipelines-export > /Users/mark/pipelines-export.log</code> 

#### Example Run
Here are snippets of an example run. Note the warnings where for a <code>V1-DRAFT</code> pipelines, no version of the pipeline was exported, and in cases where the most recent version is a <code>DRAFT</code> like </code>V2-DRAFT</code> or higher, the most recent published version was exported:

```
$ python3 export-old-pipelines.py /Users/mark/old-pipelines/old_pipelines.json /Users/mark/pipelines-export 
---------------------------------
input_file: '/Users/mark/old-pipelines/old_pipelines.json'
---------------------------------
export_dir: '/Users/mark/pipelines-export'
---------------------------------
Connecting to Control Hub
---------------------------------
Exporting Pipelines...
---------------------------------
Pipeline '146-databricks-on-azure' version '1-DRAFT' with pipeline ID '17008a20-444d-45c8-a8bc-5e7f55a8dade:8030c2e9-1a39-11ec-a5fe-97c8d4369386' is a draft pipeline and can't be exported.
Looking for the most recent published version of the pipeline...
No published versions found for this pipeline
Warning: Pipeline '146-databricks-on-azure' with pipeline ID '17008a20-444d-45c8-a8bc-5e7f55a8dade:8030c2e9-1a39-11ec-a5fe-97c8d4369386' was not exported!
---------------------------------
Pipeline '2 - Union' version '5-DRAFT' with pipeline ID '013aba98-7206-4322-80a3-674f0ed0fefa:8030c2e9-1a39-11ec-a5fe-97c8d4369386' is a draft pipeline and can't be exported.
Looking for the most recent published version of the pipeline...
Exporting pipeline '2 - Union' version '4' with pipeline ID '013aba98-7206-4322-80a3-674f0ed0fefa:8030c2e9-1a39-11ec-a5fe-97c8d4369386'into the file '/Users/mark/pipelines-export/2 - Union.zip'
streamsets-old-pipelines-cleanup/.venv/bin/python /Users/mark/Documents/GitHub/146/streamsets-old-pipelines-cleanup/python/export-old-pipelines.py /Users/mark/old-pipelines/old_pipelines.json /Users/mark/pipelines-export 
---------------------------------
input_file: '/Users/mark/old-pipelines/old_pipelines.json'
---------------------------------
export_dir: '/Users/mark/pipelines-export'
---------------------------------
Connecting to Control Hub
---------------------------------
Exporting Pipelines...
---------------------------------
Pipeline '146-databricks-on-azure' version '1-DRAFT' with pipeline ID '17008a20-444d-45c8-a8bc-5e7f55a8dade:8030c2e9-1a39-11ec-a5fe-97c8d4369386' is a draft pipeline and can't be exported.
Looking for the most recent published version of the pipeline...
No published versions found for this pipeline
Warning: Pipeline '146-databricks-on-azure' with pipeline ID '17008a20-444d-45c8-a8bc-5e7f55a8dade:8030c2e9-1a39-11ec-a5fe-97c8d4369386' was not exported!
---------------------------------
Pipeline '2 - Union' version '5-DRAFT' with pipeline ID '013aba98-7206-4322-80a3-674f0ed0fefa:8030c2e9-1a39-11ec-a5fe-97c8d4369386' is a draft pipeline and can't be exported.
Looking for the most recent published version of the pipeline...
Exporting pipeline '2 - Union' version '4' with pipeline ID '013aba98-7206-4322-80a3-674f0ed0fefa:8030c2e9-1a39-11ec-a5fe-97c8d4369386'into the file '/Users/mark/pipelines-export/2 - Union.zip'
---------------------------------
Exporting pipeline 'Excel ETL' version '1' with pipeline ID '39b27983-c1c5-4750-8625-4ce6bdeb5157:8030c2e9-1a39-11ec-a5fe-97c8d4369386'into the file '/Users/mark/pipelines-export/Excel ETL.zip'
---------------------------------
Exporting pipeline 'Excel to Snowflake' version '1' with pipeline ID 'a57161b9-916e-410f-9e8f-e6dc400907ea:8030c2e9-1a39-11ec-a5fe-97c8d4369386'into the file '/Users/mark/pipelines-export/Excel to Snowflake.zip'
---------------------------------
Exporting pipeline 'Files to Snowflake' version '5' with pipeline ID '64d52992-6d78-4ac4-8591-b71ed4d4f769:8030c2e9-1a39-11ec-a5fe-97c8d4369386'into the file '/Users/mark/pipelines-export/Files to Snowflake.zip'
---------------------------------


```

If you have Job Template Instances in the list of old Jobs, you will see messages like this when you run the script:
```
	---------------------------------
	Skipping export for Job 'Check Database Table Schema - employee' because it is a Job Template Instance
	--> Job Template ID '97ec0a88-4e19-4855-aece-3a9b13f390d7:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	---------------------------------
```
Here is a directory listing of the exported Jobs:

```
	$ ls -l ~/job-exports
	total 888
	-rw-r--r--@ 1 mark  staff   90414 Jul 23 14:43 Oracle CDC to Snowflake.zip
	-rw-r--r--@ 1 mark  staff  135891 Jul 23 14:43 Oracle to Snowflake Bulk Load.zip
	-rw-r--r--@ 1 mark  staff   52758 Jul 23 14:43 Weather Aggregation.zip
	-rw-r--r--@ 1 mark  staff  105615 Jul 23 14:43 Weather Raw to Refined (1).zip
	-rw-r--r--@ 1 mark  staff   59928 Jul 23 14:43 Weather to MongoDB.zip
```

A good test to perform at this point is to manually delete one of those Job instances from Control Hub and to import the corresponding exported file using the Control Hub UI to confirm the exported Job archives are valid, like this:

<img src="images/import1.png" alt="import1.png" width="700"/>
<img src="images/import2.png" alt="import2.png" width="700"/>


## Script #3 - delete-old-jobs.py

Description:   This script attempts to delete Jobs instances listed in the input file.  Job Instances and Job Template Instances will be deleted, unless there are permission issues, or in cases where Job instances are referenced by Sequences or Topologies. The script makes sure each Job in the input file has <code>INACTIVE</code> status and has not been run since after the <code>last_run_threshold</code>.

Args:
- <code>input_file</code> - A JSON list of Job instances to delete.

Usage:          <code>$ python3 delete-old-jobs.py <input_file></code>

Usage Example:  <code>$ python3 delete-old-jobs.py /Users/mark/old-jobs/old_jobs.json</code>

This script does not write a log, so if you want to capture the results of this script in a file, redirect its output like this:

<code>$ python3 delete-old-jobs.py /Users/mark/old-jobs/old_jobs.json > /Users/mark/deleted-jobs.log</code>

A good test to perform at this point is to manually edit an <code>old_jobs.json</code> input file so there are only a couple of Jobs listed, run the script, and confirm those Jobs are correctly deleted.


Example Run:
```
	$ python3 python/delete-old-jobs.py /Users/mark/old-jobs/old_jobs.json 
	---------------------------------
	input_file: '/Users/mark/old-jobs/old_jobs.json'
	---------------------------------
	Connecting to Control Hub
	---------------------------------
	Preparing to delete Job 'Weather to Elasticsearch' with Job ID '345b33a1-1ad6-47a0-9b66-10185921d3fc:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	Error: Job 'Weather to Elasticsearch' has status 'INACTIVE_ERROR'; the Job should have status of 'INACTIVE' to be deleted
	---------------------------------
	Preparing to delete Job 'Weather to MongoDB' with Job ID '338b33a1-1ad6-47a0-9b66-6b685921d3fc:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Last Job run was before threshold date.
	Error: Attempt to delete Job failed; JOBRUNNER_251: Cannot delete job 'Weather to MongoDB' as it is part of sequences: '1'
	---------------------------------
	Preparing to delete Job 'Weather to Astra' with Job ID '118b33a1-1ad6-47a0-9b66-6b685921d3fc:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Job was run at '2025-07-24 18:30:11' which is more recent than the last_run_threshold of '2025-06-30'
	--> Job will not be deleted.
 	---------------------------------
	Preparing to delete Job 'Check API Schema - http://localhost:9001/get/employee' with Job ID '6641429e-dea4-416e-a93a-d4bdc5f98eaf:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Last Job run was before threshold date.
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check API Schema - http://localhost:9002/movies' with Job ID '3687eba0-9a76-457c-ad5a-56424cac8181:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Last Job run was before threshold date.
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check API Schema - http://localhost:9001/get/employee' with Job ID '4082cfa9-f622-4f83-a1a1-9bacfe10a2a6:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Last Job run was before threshold date.
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check Database Table Schema - employee' with Job ID '6b3a84fd-b72f-4ab4-a2a3-10850dd3f88e:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Last Job run was before threshold date.
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check Database Table Schema - employee' with Job ID 'bf8aa913-eca9-45f6-8cea-9ce7bff82326:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Last Job run was before threshold date.
	- Job was deleted.
	---------------------------------
	Done
```


