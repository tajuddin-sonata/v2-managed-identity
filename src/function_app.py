import logging
import json
import requests
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="EventGridTrigger")
@app.event_grid_trigger(arg_name="event")
def main(event: func.EventGridEvent):
    result = json.dumps({
        'id': event.id,
        'data': event.get_json(),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
        'event_time': str(event.event_time),
    })

    logging.info('Python EventGrid trigger processed an event: %s', result)

    parsed_json = json.loads(result)

    if 'landing' in event.subject.lower():

        logic_app_url = "$LOGICAPP_CALLBACK_URL"

        response = requests.post(logic_app_url, json=parsed_json)

        if response.status_code >= 200 and response.status_code < 300:
            logging.info(f"Output sent to Logic App successfully. Status code: {response.status_code}, Response content: {response.text}")
        else:
            logging.info(f"Failed to send output to Logic App. Status code: {response.status_code}, Response content: {response.text}")
    else:
        logging.info('Event subject does not contain "landing". Skipping processing.')