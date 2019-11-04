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

        # attempt to send data to blynk
        try:    
            response = requests.get(URL)
        except requests.exceptions.RequestException as e:
            logging.error(e)
    else:
        # either mac or the feedname is not found, skipping
        logging.error("Not sure what to do with " + str(dest_feedname) + " from " + str(dest_mac_address))

# set our default log level
logging.basicConfig(level=logging.INFO)

# initialize the config parser
config = configparser.ConfigParser()                                     
config.read('./settings.ini')

# setup the server once
udp_server_socket = init_udp_server()

# both the blynk url and the auth token must be present
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

'''
Let's get the infinite loop going.
Essentially, udp_server_socket.recvfrom(1024) will block, waiting for a new message.
Once the message is received, we need to:
1. make sure it's actually JSON
2. make sure all the required fields are present
3. publish to blynk
4. (optionally) do what else needs to be done
'''
while(True):
    bytesAddressPair = udp_server_socket.recvfrom(1024)

    # this is the actual message
    message = bytesAddressPair[0]

    # source IP addressed, ignored for now
    address = bytesAddressPair[1]

    '''
    First, make sure the udp payload is a valid json string.
    If it is, valid_json is set to True and message contains the JSON object.
    We do it in one shot since we are much more likely to get valid JSON than not.
    If not, valid_json is set to False and message is an empty string ''.
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

    '''
    Let's get all the things assigned to the right values:
    - value is the actual numeric value of the sensor
    - mac is the mac address, this is how we figure out what to route where
    - feed name is used to look up the blynk virtual pin
    '''
    value = client_message["value"]
    mac   = client_message["mac"]
    feed_name = client_message["feedName"]
    
    '''
    Publish the data to blynk.
    NOTE: we don't know the correct pin, we'll look it up later
    '''
    send_value_to_blynk(mac, feed_name, value)
