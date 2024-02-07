###############################################
#############  Sample Curl ####################
###############################################

#!/bin/bash

# Replace with your Azure Function App URL
###"https://<function-app-name>.azurewebsites.net/api/<function-key>"
function_url="https://<function-app-name>.azurewebsites.net/api/<function-key>"

# Replace with your Azure Function App key or any other authentication mechanism
api_key="<function-key>"  ###"Function-key"
set -x

curl -m 59 -X POST "$function_url" -H "x-functions-key: $api_key" -H "Content-Type: application/json" -d '{"context": {"azure_subscription": "dev-sub","azure_location": "east us","client_id": "customer1","execution_id": "id-1234","execution_start": "2024-01-19T03:52:20Z"},"input_files": {"source_file": {"bucket_name": "247ai-stg-cca-customer1-audio-landing","full_path": "test.wav","version": "0x8DC18A209B13338","uploaded": "2024-01-19T09:22:20Z"}},"function_config": {"label_tags": {"client": "ci_client","step": "ci_step","type": "ci_media_type"},"functions": {"deepgram": ["deepgram"],"process-audio": ["process-audio"],"process-metadata": ["process-metadata"],"process-transcript": ["process-transcript"],"process-video": ["process-video"],"redact-audio": ["redact-audio"]},"config_bucket_name": "247ai-stg-cca"}}'

#####################################
#################### OR #############
#!/bin/bash

# Replace with your Azure Function App URL
###"https://<function-app-name>.azurewebsites.net/api/<function-key>"
function_url="https://<function-app-name>.azurewebsites.net/api/<function-key>"

# Replace with your Azure Function App key or any other authentication mechanism
api_key="<function-key>"  ###"Function-key"
set -x

curl -m 59 -X POST "$function_url" \
-H "x-functions-key: $api_key" \
-H "Content-Type: application/json" \
-d '{
    "context": {
        "azure_subscription": "dev-sub",
        "azure_location": "east us",
        "client_id": "customer1",
        "execution_id": "id-1234",
        "execution_start": "2024-01-19T03:52:20Z"
    },
    "input_files": {
        "source_file": {
            "bucket_name": "247ai-stg-cca-customer1-audio-landing",
            "full_path": "test.wav",
            "version": "0x8DC18A209B13338",
            "uploaded": "2024-01-19T09:22:20Z"
        }
    },
    "function_config": {
        "label_tags": {
            "client": "ci_client",
            "step": "ci_step",
            "type": "ci_media_type"
        },
        "functions": {
            "deepgram": ["deepgram"],
            "process-audio": ["process-audio"],
            "process-metadata": ["process-metadata"],
            "process-transcript": ["process-transcript"],
            "process-video": ["process-video"],
            "redact-audio": ["redact-audio"]
        },
        "config_bucket_name": "247ai-stg-cca"
    }
}'
