import configparser
import socket
import sys
import jsonschema
from jsonschema import validate
import json
import logging
import requests
import os

def init_udp_server():
    # all interefaces
    HOST = ""

    # port to listen on
    PORT = 3333

    # Datagram (udp) socket
    try:
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logging.info("Socket created")
    except OSError as err:
        logging.error("OS error: {0}".format(err))
        sys.exit()

    # Bind socket to host and port
    try:
        UDPServerSocket.bind((HOST, PORT))
    except OSError as err:
        logging.error("OS error: {0}".format(err))	
        sys.exit()

    logging.info("UDP server is ready to go.")

    return UDPServerSocket

def validate_json_schema(payload):
    '''
    In a JSON Schema, by default properties are not required, all that our schema does 
    is state what type they must be if the property is present. 
    So for validation to flag whatever additional properties are missing, 
    we need to mark that key as a required property first, 
    by adding a required list with names. For more info:
    https://json-schema.org/understanding-json-schema/reference/object.html#required-properties

    Note the "required" property at the end of the schema.
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
        validate(payload, schema)
        return True
    except jsonschema.exceptions.ValidationError as ve:
        #sys.stderr.write(str(ve) + "\n")
        logging.error(ve)
        return False

def is_valid_json(udp_payload):
    # make sure we were actually passed a JSON object
    try:
        json_payload = json.loads(message)
        payload_is_json = True
    except:
        json_payload = ''
        payload_is_json = False
    
    # return a tuple of boolean and JSON payload
    return payload_is_json, json_payload

def send_value_to_blynk(dest_mac_address, dest_feedname, dest_value):
    # check to see if there's a section and that section has the pin
    if config.has_option(dest_mac_address,dest_feedname):
        # it does, let's grab its pin
        pin = config[dest_mac_address][dest_feedname]

        # format the URL properly. This is a REST call to blynk.
        URL = BLYNK_URL + BLYNK_AUTH + '/update/V' + str(pin) + '?value=' + str(value)
        logging.info("Sending " + str(value) + " to pin " + str(pin))

        try:    
            response = requests.get(URL)
        except requests.exceptions.RequestException as e:
            logging.error(e)
    else:
        # either mac or the feedname is not found, skipping
        logging.error("Not sure what to do with " + str(dest_feedname) + " from " + str(dest_mac_address))


''' We need to make sure the env vars are set correctly.
Assuming loglevel is bound to the string value obtained from the
command line argument. Convert to upper case to allow the user to
specify --log=DEBUG or --log=debug
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
logging.basicConfig(level=numeric_level)
'''

logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()                                     
config.read('./settings.ini')

# setup the server once
udp_server_socket = init_udp_server()

for env_var in ('BLYNK_URL','BLYNK_AUTH'):
    logging.info("Checking for " + str(env_var))
    if env_var in os.environ:
        logging.info("Found " + str(env_var))
    else:
        logging.error("Missing required environment variable: " + str(env_var))
        sys.exit(1)

# blynk settings
BLYNK_AUTH = os.getenv("BLYNK_AUTH")
BLYNK_URL = os.getenv("BLYNK_URL")

while(True):
    bytesAddressPair = udp_server_socket.recvfrom(1024)

    message = bytesAddressPair[0]
    address = bytesAddressPair[1]

    '''
    First, make sure the udp payload is a valid json string.
    If it is, valid_json is set to True and message contains the JSON object.
    If not, valid_json is set to False and message is ''
    '''
    valid_json_bool, client_message = is_valid_json(message)

    # only validate the schema if the message is a valid json
    if (valid_json_bool):
        # OK, so it is JSON. Let's make sure it is semantically valid
        if (validate_json_schema(client_message)):
            logging.info("Valid schema detected!")
        else:
            logging.error("Failed schema validation, skipping.")
            continue
    else:
        logging.error("Could not serialize payload to JSON, skipping.")
        continue
    
    # print the received message for debugging purposes
    logging.debug(client_message)

    #sensor_data = json.loads(client_message)
    value = client_message["value"]
    mac   = client_message["mac"]
    feed_name = client_message["feedName"]
    
    send_value_to_blynk(mac, feed_name, value)
