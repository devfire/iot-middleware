import os
import settings
import sys

def validate_settings():
    # both the blynk url and the auth token must be present
    for env_var in ('BLYNK_URL','BLYNK_AUTH'):
        settings.logging.info("Checking for " + str(env_var))
        if env_var in os.environ:
            settings.logging.info("Found " + str(env_var))
        else:
            settings.logging.error("Missing required environment variable: " + str(env_var))
            sys.exit(1)

def validate_json_schema(payload):
    valid_json_schema = None
    settings.logging.info("Validating " + str(payload))
    try:
        settings.jsonschema.validate(payload, settings.schema)
        valid_json_schema = True
    except settings.jsonschema.exceptions.ValidationError as ve:
        settings.logging.error(ve)
        valid_json_schema = False
    return valid_json_schema

def is_valid_json(udp_payload):
    payload_is_json = None
    settings.logging.info("Validating " + str(udp_payload))
    # make sure we were actually passed a JSON object
    try:
        json_payload = json.loads(udp_payload)
        payload_is_json = True
    except:
        json_payload = ''
        payload_is_json = False
    
    # return a tuple of boolean and JSON payload
    return payload_is_json, json_payload