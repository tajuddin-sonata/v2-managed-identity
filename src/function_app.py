from time import time as t1
from uuid import uuid1
import logging
from datetime import datetime, timedelta, timezone
from json import dumps, loads
from pathlib import Path
import functions_framework
from flask import abort, g, make_response
from flask_expects_json import expects_json
from os import environ
import os
import sys
import requests
import json
import datetime as d
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from azure_normalize import custom_serializer,normalize

from util_input_validation import schema, Config
from util_helpers import impersonate_account, create_outgoing_file_ref, handle_bad_request,handle_exception,handle_not_found
# from deepgram import Deepgram
# from normalize import normalise_deepgram

#Libraries for Azure
import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from werkzeug.exceptions import InternalServerError, BadRequest, NotFound


### GLOBAL Vars

### Env Vars
### service = environ.get("K_SERVICE")

### Instance-wide storage Vars
instance_id = str(uuid1())
run_counter = 0

start_time = t1()  
time_cold_start = t1() - start_time

# connection_string=os.environ["StorageAccountConnectionString"]
# storage_client=BlobServiceClient.from_connection_string(connection_string)

#### curl check
import subprocess

# def execute_curl(url):
#     try:
#         # Run the curl command and capture the output
#         result = subprocess.run(['curl', '-I', url], capture_output=True, text=True, check=True)

#         # Print the result (headers) of the curl command
#         print(result.stdout)

#         # Check the return code to determine success or failure
#         if result.returncode == 0:
#             print("Curl command executed successfully")
#         else:
#             print(f"Curl command failed with return code: {result.returncode}")

#     except subprocess.CalledProcessError as e:
#         # Handle exceptions, if the curl command fails
#         print(f"Error executing curl command: {e}")
#         print("Error output:")
#         print(e.stderr)
    
# # Example usage
# url_to_check = "http://stg-deepgram.dg.stg.usw1.cloud.247-inc.net:8080/v2"
# execute_curl(url_to_check)


### MAIN
app = func.FunctionApp()
@app.function_name(name="wf_transcribe_stt_HttpTrigger1")
@app.route(route="wf_transcribe_stt_HttpTrigger1")

# @functions_framework.http
# @expects_json(schema)
def main(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    ### Input Variables
    global run_counter
    run_counter += 1
    request_recieved = datetime.now(timezone.utc)
    request_json = req.get_json()
    CONFIG = Config(request_json)
    del request_json
    context_json = {
        **CONFIG.context.toJson(),
        "instance": instance_id,
        "instance_run": run_counter,
        "request_recieved": request_recieved.isoformat(),
    }
    logging.info(f'Received request: {context_json}')

    account_url = CONFIG.context.storageaccounturl
    storage_client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())

    ### Output Variables
    response_json = {}
    out_files = {}

    audio_blob = storage_client.get_container_client(CONFIG.input_files.audio.bucket_name).get_blob_client(
        CONFIG.input_files.audio.full_path, #version_id=CONFIG.input_files.audio.version
    )

    try: 
        ### Try to fetch blob properties with the condition that the ETag must match the desired_etag
        etag_value = audio_blob.get_blob_properties(if_match=CONFIG.input_files.audio.version)
        logging.info(f'Audio Blob Name: {audio_blob.blob_name}')
        logging.info(f'Audio Blob ETag: {etag_value["etag"]}')

    except ResourceNotFoundError:
        ### Handle the case where the blob with the specified ETag is not found
        abort(404, "Media file not found on bucket")


    ###################################################
    #####  Generate Shared Access Signature (SAS) Token
    ###################################################
        
    ### Call the function to get the impersonated credentials
    # credentials = impersonate_account(CONFIG.function_config.signing_account, 3600)
    
    ### Get user delegation key
    user_delegation_key = storage_client.get_user_delegation_key(
        key_start_time=datetime.utcnow(),
        key_expiry_time=datetime.utcnow() + timedelta(minutes=30),
    )
    ### If blob exists, Generate Shared Access Signature (SAS) Token
    sas_token = generate_blob_sas(
        account_name=storage_client.account_name,
        account_key=None,  
        token_credential=impersonate_account(CONFIG.function_config.signing_account, 3600),
        # token_credential=credentials["token"],  ## Use the token obtained from impersonation
        container_name=CONFIG.input_files.audio.bucket_name,
        blob_name=CONFIG.input_files.audio.full_path,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=30),
        user_delegation_key=user_delegation_key, 
    )

    audio_blob_url = audio_blob.url
    logging.info(f'Media Blob URL: {audio_blob_url}')

    ### Combine the blob URL with the SAS token to get the signed URL
    target_media_signed_url = f"{audio_blob_url}?{sas_token}"
    ### Logging the staged_media_signed_url
    logging.info(f"Target Media Signed URL: {target_media_signed_url}")
    

    azure_opts = {"api_key": "", "region": ""}

    if CONFIG.function_config.asr_config.api_key is not None:
        print("Found_Azure_API_KEY")
        azure_opts["api_key"] = str(CONFIG.function_config.asr_config.api_key)
        if CONFIG.function_config.asr_config.region is not None:
            print("region")
            azure_opts["region"] = str(CONFIG.function_config.asr_config.region)
            if CONFIG.function_config.asr_config.end_point is not None:
                print("end_point")
                azure_opts["end_point"] = str(CONFIG.function_config.asr_config.end_point)
    logging.info(azure_opts)

    service_region=azure_opts["region"]
    subscription_key=azure_opts["api_key"]
    end_point=azure_opts["end_point"]
    logging.info(f"subscription_key:{subscription_key}")

    # Assuming target_media_signed_url is defined elsewhere in your code
    source = {'url': target_media_signed_url}
    params = {
        feature: 
            True if str(val).lower()=='true'
            else False if str(val).lower()=='false'
            else int(val) if isinstance(val,str) and is_integer(val)
            else float(val) if isinstance(val,str) and is_float(val)
            else val
            for feature, val in CONFIG.function_config.asr_config.features.items()
        } if CONFIG.function_config.asr_config.features!=None else {}
    
    logging.info(f"source:{source}")
    logging.info(f"params:{params}")

    url_for_post = f"https://{end_point}/speechtotext/v3.1/transcriptions"

    headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key
    }
    logging.info(f"headers:{headers}")

    body = {
    "contentUrls": [target_media_signed_url],
    "properties": params,
    "locale": "en-US",
    "displayName": "Transcription"
    }
    logging.info(f"body:{body}")

    result_from_post = requests.post(url_for_post, headers=headers, data=json.dumps(body))
    start_time_stt=d.datetime.now()
    logging.info(f"start_time:{start_time_stt}")
    response_json = json.loads(result_from_post.text)
    logging.info(f"result_from_post:{response_json}")

    transcription_id = response_json["self"].split('/')[-1]
    logging.info(f"transcription_id:{transcription_id}")
    model=response_json["model"]['self'].split('/')[-1]
    logging.info(f"model:{model}")
    version=response_json['self'].split('/')[-3]
    logging.info(f"version:{version}")

    files = response_json["links"]["files"]
    url_for_transcript_file = files
    while True:
        result_from_1st_get = requests.get(url_for_transcript_file, headers=headers)
        response_json = json.loads(result_from_1st_get.text)
        if response_json.get('values'):
            files = response_json['values']
            break
        else:
            logging.info("No values found. Retrying in 10 seconds.")
            time.sleep(10)
    file1 = files[0]
    content_url = file1.get('links', {}).get('contentUrl')
    if content_url:
        result_from_2nd_get = requests.get(content_url, headers=headers)
        end_time_stt=d.datetime.now()
        logging.info(f"end_time:{end_time_stt}")
        logging.info(f"total_time_taken:{end_time_stt-start_time_stt}")
        logging.info(f"result_from_2nd_get: {result_from_2nd_get.text}")
        azure_stt_response = json.loads(result_from_2nd_get.text)
        azure_normalized=normalize(azure_stt_response, transcription_id, model, version,CONFIG.function_config.transcript_config.toJson())
        logging.info(f"normalized:{azure_normalized}")

        normalized_format = json.dumps(azure_normalized, default=custom_serializer)
        logging.info(f"normalized_format:{normalized_format}")
    
    ### Upload Normalized Transcript to Stage bucket
    staging_transcript_path = (
        Path(
            CONFIG.staging_config.folder_path,
            str(CONFIG.staging_config.file_prefix) + "_" + "transcript",
        )
        .with_suffix('.json')
        .as_posix()
    )
    staging_transcript_blob = storage_client.get_container_client(CONFIG.staging_config.bucket_name).get_blob_client(
        staging_transcript_path
    )

    staging_transcript_blob.upload_blob(dumps(normalized_format), content_type='application/json', overwrite=True)
    if not staging_transcript_blob.exists():
        abort(500,'transcript failed to upload to staging bucket')

    out_files["transcript"] = create_outgoing_file_ref(staging_transcript_blob)
    
    ### Return with all the locations
    response_json["status"] = "success"
    response_json["staged_files"] = out_files
    # return make_response(response_json, 200)
    logging.info(f"response_json_output: {response_json}")
    return func.HttpResponse(body=dumps(response_json), status_code=200, mimetype='application/json')


def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
    
def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False