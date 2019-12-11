import os
import settings
import sys
import json

def validate_env_variables():
    # both the blynk url and the auth token must be present
    for env_var in ('BLYNK_URL','BLYNK_AUTH'):
        settings.logger.info("Checking for " + str(env_var))
        if env_var in os.environ:
            settings.logger.info("Found " + str(env_var))
        else:
            settings.logger.error("Missing required environment variable: " + str(env_var))
            sys.exit(1)

def validate_config_file():
    # make sure the config file actually exists
    try:
        settings.config.read_file(open(settings.CONFIG_FILE))
    except FileNotFoundError:
        settings.logger.error("Missing config file, exiting.")
        sys.exit(1)

def validate_json_schema(payload):
    valid_json_schema = None
    settings.logger.debug("Validating " + str(payload))
    try:
        settings.jsonschema.validate(payload, settings.schema)
        valid_json_schema = True
    except settings.jsonschema.exceptions.ValidationError as ve:
        settings.logger.error(ve)
        valid_json_schema = False
    return valid_json_schema

def validate_json(udp_payload):
    payload_is_json = None
    settings.logger.debug("Validating " + str(udp_payload))
    # make sure we were actually passed a JSON object
    try:
        json_payload = json.loads(udp_payload)
        settings.logger.debug("Valid JSON detected " + str(udp_payload))
        payload_is_json = True
    except:
        json_payload = ''
        settings.logger.error("Invalid JSON detected " + str(udp_payload))
        payload_is_json = False
    
    # return a tuple of boolean and JSON payload
    return payload_is_json, json_payload