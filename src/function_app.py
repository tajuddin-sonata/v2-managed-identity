import azure.functions as func
import logging
from datetime import datetime, timezone
from time import time
start_time = time()  
from uuid import uuid1
from io import StringIO
from pathlib import Path, PurePath
from dotenv import dotenv_values
import functions_framework
from flask import Request, g
from flask_expects_json import expects_json
from os import environ
from json import dumps, loads
import requests

# Azure Function Imports
import os
import sys
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from werkzeug.exceptions import NotFound

# sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from util_input_validation import schema, Config
from util_helpers import handle_bad_request, handle_exception


# Env Vars
# service = environ.get("K_SERVICE")  
# service = os.environ.get("FUNCTIONS_WORKER_RUNTIME")  

# connection_string = os.environ['StorageAccountConnectionString']
# storage_client = BlobServiceClient.from_connection_string(connection_string)

# Instance-wide storage Vars
instance_id = str(uuid1())
run_counter = 0
time_cold_start = time() - start_time

app = func.FunctionApp()
@app.function_name(name="wf_configure_HttpTrigger1")
@app.route(route="wf_configure_HttpTrigger1")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    global run_counter
    run_counter += 1
    request_recieved = datetime.now(timezone.utc)
    request_json = req.get_json()
    CONFIG = Config(request_json)
    del request_json
    context = {
        **CONFIG.context.toJson(), 
        "instance": instance_id,
        "instance_run": run_counter,
        "request_recieved": request_recieved.isoformat(),
    }
    logging.info(f'Received request: {context}')

    account_url = CONFIG.context.storageaccounturl
    storage_client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())

    response_json = {
        "client_buckets": None,
        "client_config": None,
        "staging_folder_path": None,
        "interaction_id": None,
        "status": "error",
    }

    # Get Config Bucket
    config_bucket = storage_client.get_container_client(CONFIG.function_config.config_bucket_name)

    if CONFIG.function_config.label_tags:
        # Find Client's Buckets by label
        landing, staging, content = find_client_buckets(
            storage_client,
            CONFIG.function_config.config_bucket_name,
            CONFIG.function_config.label_tags,
            CONFIG.context.client_id,
        )

        response_json["client_buckets"] = {
            "landing": landing.name if landing else None,
            "staging": staging.name if staging else None,
            "content": content.name if content else None,
        }

    if CONFIG.function_config.functions:
        merged_config = get_config(
            config_bucket, CONFIG.context.client_id, CONFIG.function_config.functions
        )
        response_json["client_config"] = merged_config

        # Generate Staging Folder path
    if (
        CONFIG.input_files
        and CONFIG.input_files.source_file.uploaded
        ):
        interaction_id, staging_folder_path, content_folder_path = generate_staging_folder_details(
            CONFIG.context,
            CONFIG.input_files.source_file,
            request_recieved
        )
        response_json["staging_folder_path"] = staging_folder_path
        response_json["content_folder_path"] = content_folder_path
        response_json["interaction_id"] = interaction_id

        # # Return with all the configuration info
        # response_json["status"] = "success"
        # return response_json, 200
        # except Exception as e:
        #     return handle_exception(e,CONFIG.context.toJson(),{x:y for x,y in CONFIG.toJson().items() if x !='context'})
   
    # Return with all the configuration info
    response_json["status"] = "success"
    return func.HttpResponse(dumps(response_json), mimetype="application/json", status_code=200)


def get_config(
    config_bucket: BlobServiceClient,
    client_id: str,
    functions: Config.FunctionConfig.Functions,
):
    ### Find config for requested functions
    config_list = {}
    ### Create Struct to hold config i.e. {"deepgram":None, "process-transcript":None}
    for function_name, config_array in functions.items():
        for item in config_array:
            config_list[item] = None

    for config_item in config_list.keys():
        # Pull Config from bucket
        config_list[config_item] = get_client_function_config(
            config_bucket, client_id, config_item
        )
    ### Now iterate through the original configuration requests,
    ### and merge all of the found config in the order of the arrays
    merged_config = {}
    for function_name, config_array in functions.items():
        merged = {}
        for item in config_array:
            merged = {
                **merged,
                **(config_list[item] if config_list[item] else {}),
            }
        merged_config[function_name] = merged
    return merged_config


def generate_staging_folder_details(context: Config.Context, source_file: Config.InputFiles.InputFile, request_recieved: datetime):
    interaction_id = Path(source_file.full_path).stem
    if source_file.uploaded:
        trigger_file_upload_time = source_file.uploaded
        staging_folder_path = Path(
            str(trigger_file_upload_time.year),
            str(trigger_file_upload_time.month).zfill(2),
            str(trigger_file_upload_time.day).zfill(2),
            str(interaction_id),
            str(str(context.execution_start.strftime("%Y%m%d%H%M%S")) if context.execution_start else str(request_recieved.strftime("%Y%m%d%H%M%S")))
            + "_" 
            + str(str(context.execution_id) if context.execution_id else str(source_file.version))
        ).as_posix()
        content_folder_path=Path(
            str(interaction_id),
            str(str(context.execution_start.strftime("%Y%m%d%H%M%S")) if context.execution_start else str(request_recieved.strftime("%Y%m%d%H%M%S")))
            + "_" 
            + str(str(context.execution_id) if context.execution_id else str(source_file.version))
        ).as_posix()
    else:
        staging_folder_path = None
        content_folder_path = None

    return interaction_id, staging_folder_path, content_folder_path


def find_client_buckets(
    
    storage_client: BlobServiceClient,
    bucket_prefix: str,
    label_tags: Config.FunctionConfig.LabelTags,
    client_id: str,
):
    landing = None
    staging = None
    content = None
    buckets = storage_client.list_containers(name_starts_with=bucket_prefix, include_metadata=True)
    
    for bucket in [
        bucket
        for bucket in buckets
        if label_tags.client in bucket.metadata
        and bucket.metadata[label_tags.client] == client_id
        and label_tags.step in bucket.metadata
    ]:
        if bucket.metadata[label_tags.step] == "landing":
            landing = bucket
        elif bucket.metadata[label_tags.step] == "staging":
            staging = bucket
        elif bucket.metadata[label_tags.step] == "content":
            content = bucket
    return landing, staging, content


def get_client_function_config(
    bucket: BlobServiceClient, client_id: str, config_item: str
):
    releases_folder = PurePath(
        "config", "config-releases", client_id, config_item
    ).as_posix()
    in_use_path = PurePath(releases_folder, "in_use").with_suffix(".sh").as_posix()
    in_use_blob = bucket.get_blob_client(in_use_path)   
    # if not in_use_blob.exists():  
    if not in_use_blob:
        return None
    
    ### Use download_blob to get the blob content
    in_use_blob = in_use_blob.download_blob().readall()
    in_use_vars = dotenv_values(stream=StringIO(in_use_blob.decode()))

    if "DEPLOY_RELEASE_VERSION" not in in_use_vars:
        return None
    target_release_folder = PurePath(
        releases_folder, str(in_use_vars["DEPLOY_RELEASE_VERSION"])
    ).as_posix()
    target_config_path = (
        PurePath(target_release_folder, "config").with_suffix(".json").as_posix()
    )
    config_blob = bucket.get_blob_client(target_config_path)
    if not config_blob:
        return None
     
    ### Use download_blob to get the config blob content   
    config_blob = config_blob.download_blob()
    return loads(config_blob.readall().decode())