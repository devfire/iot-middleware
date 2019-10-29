import socket
import sys
import jsonschema
from jsonschema import validate
import json
import logging
import requests

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

    logging.info("UDP server is ready to go!")

    return UDPServerSocket

def validate_json_schema(payload):
    '''
    In a JSON Schema, by default properties are not required, all that our schema does is state what type they must be if the property is present. 
    So for validation to flag whatever additional properties are missing, we need to mark that key as a required property first, 
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
        return False

def check_valid_json(udp_payload):
    # make sure we were actually passed a JSON object
    try:
        json_payload = json.loads(message)
        payload_is_json = True
    except:
        json_payload = ''
        payload_is_json = False
    
    # return a tuple of boolean and JSON payload
    return payload_is_json, json_payload

def convert_mac_to_name(json_payload):
    pass

def send_value_to_blynk(pin, value):
    # blynk auth token
    BLYNK_AUTH = 'qVzQ9p19MoOzZ1xVX2jCLWnS7xe1N7_e'
    BASE_URL = 'http://blynk-cloud.com/'

    URL = BASE_URL + BLYNK_AUTH + '/update/V' + str(pin) + '?value=' + str(value)
    logging.info("Sending " + str(value) + "to pin " + str(pin))

    try:
        response = requests.get(URL)
    except requests.exceptions.RequestException as e:
        print e
    
# setup the server once
udp_server_socket = init_udp_server()

while(True):
    bytesAddressPair = udp_server_socket.recvfrom(1024)

    message = bytesAddressPair[0]
    address = bytesAddressPair[1]

    '''
    First, make sure the udp payload is a valid json string.
    If it is, valid_json is set to True and message contains the JSON object.
    If not, valid_json is set to False and message is ''
    '''
    valid_json, client_message = check_valid_json(message)

    # only validate the schema if the message is a valid json
    if (valid_json):
        # OK, so it is JSON. Let's make sure it is semantically valid
        if (validate_json_schema(client_message)):
            logging.info("Valid schema detected!")
        else:
            logging.error("Failed schema validation, skipping.")
            continue
    else:
        logging.error("Could not serialize payload to JSON, skipping.")
        continue
    
    send_value_to_blynk(1,123)
