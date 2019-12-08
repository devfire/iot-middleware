import configparser
import socket
import sys
import jsonschema
import json
import logging
import requests
import os

# Create a custom logger
handler = logging.StreamHandler()
c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(c_format)
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
logger.addHandler(handler)

# set the default config file
CONFIG_FILE = 'settings.ini'

def init_udp_server():
    # listen on all interefaces
    HOST = ""

    # port to listen on
    PORT = 3333111

    # Datagram (udp) socket
    try:
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.debug("Socket created")
    except OSError as err:
        logger.error(err)
        sys.exit()

    # Bind socket to host and port
    try:
        UDPServerSocket.bind((HOST, PORT))
    except OverflowError as err:
        logger.error(err)	
        sys.exit()

    logger.info("UDP server is ready to go.")

    return UDPServerSocket

def validate_json_schema(payload):
    '''
    In a JSON Schema, by default properties are not required, all that our schema does 
    is state what type they must be if the property is present. 
    So, for validation to flag whatever additional properties are missing, 
    we need to mark that key as a required property first, 
    by adding a required list with names. For more info:
    https://json-schema.org/understanding-json-schema/reference/object.html#required-properties

    NOTE: the "required" property is at the end of the schema.
    '''
    schema = {
        "type" : "object",
        "properties" : {
            "mac" : {"type" : "string"},
            "feedName" : {"type" : "string"},
            "value" : {"type" : "number"},
        },
        "required": ["mac", "feedName", "value"]
    }

    try:
        jsonschema.validate(payload, schema)
        return True
    except jsonschema.exceptions.ValidationError as ve:
        #sys.stderr.write(str(ve) + "\n")
        logger.error(ve)
        return False

def is_valid_json(udp_payload):
    # make sure we were actually passed a JSON object
    try:
        json_payload = json.loads(udp_payload)
        payload_is_json = True
    except:
        json_payload = ''
        payload_is_json = False
    
    # return a tuple of boolean and JSON payload
    return payload_is_json, json_payload

def send_value_to_blynk(client_message):
    # blynk settings
    BLYNK_AUTH = os.getenv("BLYNK_AUTH")
    BLYNK_URL = os.getenv("BLYNK_URL")

    '''
    Let's get all the things assigned to the right values:
    - value is the actual numeric value of the sensor
    - mac is the mac address, this is how we figure out what to route where
    - feed name is used to look up the blynk virtual pin
    '''
    value = client_message["value"]
    mac   = client_message["mac"]
    feed_name = client_message["feedName"]

    logger.debug("Checking the config file for the pin settings")
    # check to see if there's a relevant section in settings.ini and that section has the pin
    if config.has_option(mac,feed_name):
        # it does, let's grab its pin
        pin = config[mac][feed_name]
        logger.debug("Found valid config for pin " + str(pin))

        # format the URL properly. This is a REST call to blynk.
        URL = BLYNK_URL + '/' + BLYNK_AUTH + '/update/V' + str(pin) + '?value=' + str(value)
        logger.debug("Posting to " + URL)

        # attempt to send data to blynk
        try:    
            response = requests.get(URL)
            logger.debug("Sent data successfully to " + URL)
        except requests.exceptions.RequestException as err:
            logger.error(err)
    else:
        # either mac or the feedname is not found, skipping
        logger.error("Not sure what to do with " + str(feed_name) + " from " + str(mac))

def validate_env_variables():
    # make sure all of the necessary env variables are defined
    logger.debug("Validating settings.")
    
    # both the blynk url and the auth token must be present
    for env_var in ('BLYNK_URL','BLYNK_AUTH'):
        logger.debug("Checking for " + str(env_var))
        if env_var in os.environ:
            logger.debug("Found " + str(env_var))
        else:
            logger.error("Missing required environment variable: " + str(env_var))
            sys.exit(1)

def initial_setup():
    # initialize the config parser
    logger.debug("Initializing the config parser.")
    config = configparser.ConfigParser()

    # make sure the settings file actually exists
    try:
        config.read_file(open(CONFIG_FILE))
    except FileNotFoundError:
        logger.error("Missing config file, exiting.")
        sys.exit(1)

'''
Let's get the infinite loop going.
Essentially, udp_server_socket.recvfrom(1024) will block, waiting for a new message.
Once the message is received, we need to:
1. make sure it's actually JSON
2. make sure all the required fields are present
3. publish to blynk
4. (optionally) do what else needs to be done
'''
def infinite_loop(udp_server_socket):
    logger.debug("Starting the processor main loop.")
    while(True):
        bytesAddressPair = udp_server_socket.recvfrom(1024)

        # this is the actual message
        message = bytesAddressPair[0]

        # source IP addressed, ignored for now
        address = bytesAddressPair[1]

        logger.debug("Received " + str(message) + "from " + str(address))

        '''
        First, make sure the udp payload is a valid json string.
        If it is, valid_json is set to True and message contains the JSON object.
        We do it in one shot since we are much more likely to get valid JSON than not.
        If not, valid_json is set to False and message is an empty string ''.
        '''
        valid_json_bool, current_client_message = is_valid_json(message)

        # only validate the schema if the message is a valid json
        if (valid_json_bool):
            # OK, so it is JSON. Let's make sure it is semantically valid
            if (validate_json_schema(current_client_message)):
                logger.debug("Valid schema detected!")
            else:
                logger.error("Failed schema validation, skipping.")
                continue # go to the beginning of the while loop
        else:
            logger.error("Could not serialize payload to JSON, skipping.")
            continue # go to the beginning of the while loop
        
        # print the received message for debugging purposes
        logger.debug(current_client_message)
        
        '''
        Publish the data to blynk.
        NOTE: we don't know the correct pin, we'll look it up later
        '''
        send_value_to_blynk(current_client_message)

if __name__ == '__main__':
    validate_env_variables()
    infinite_loop(init_udp_server())