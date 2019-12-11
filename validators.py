import os
import shared
import sys
import json

def validate_env_variables():
    # both the blynk url and the auth token must be present
    for env_var in ('BLYNK_URL','BLYNK_AUTH'):
        shared.logger.debug("Checking for " + str(env_var))
        if env_var in os.environ:
            shared.logger.debug("Found " + str(env_var))
        else:
            shared.logger.error("Missing required environment variable: " + str(env_var))
            sys.exit(1)

def validate_config_file():
    # make sure the config file actually exists
    try:
        shared.config.read_file(open(shared.CONFIG_FILE))
    except FileNotFoundError:
        shared.logger.error("Missing config file, exiting.")
        sys.exit(1)

def validate_json_schema(payload):
    valid_json_schema = None
    shared.logger.debug("Validating " + str(payload))
    try:
        shared.jsonschema.validate(payload, shared.schema)
        valid_json_schema = True
    except shared.jsonschema.exceptions.ValidationError as ve:
        shared.logger.error(ve)
        valid_json_schema = False
    return valid_json_schema

def validate_json(udp_payload):
    payload_is_json = None
    shared.logger.debug("Validating " + str(udp_payload))
    # make sure we were actually passed a JSON object
    try:
        json_payload = json.loads(udp_payload)
        shared.logger.debug("Valid JSON detected " + str(udp_payload))
        payload_is_json = True
    except:
        json_payload = ''
        shared.logger.error("Invalid JSON detected " + str(udp_payload))
        payload_is_json = False
    
    # return a tuple of boolean and JSON payload
    return payload_is_json, json_payload