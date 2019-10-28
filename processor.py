import socket
import sys
import jsonschema
from jsonschema import validate
import json

def init_udp_server():
    # all interefaces
    HOST = ""

    # port to listen on
    PORT = 3333

    # Datagram (udp) socket
    try:
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Socket created")
    except OSError as err:
        print("OS error: {0}".format(err))
        sys.exit()


    # Bind socket to host and port
    try:
        UDPServerSocket.bind((HOST, PORT))
    except OSError as err:
        print("OS error: {0}".format(err))	
        sys.exit()

    print("UDP server is ready to go!")

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
        sys.stderr.write(str(ve) + "\n")
        return False

def check_valid_json(udp_payload):
    # First, let's make sure we were actually passed a JSON object
    try:
        json_payload = json.loads(message)
        payload_is_json = True
    except:
        print("Could not serialize payload to JSON, skipping.")
        payload_is_json = False
        json_payload = ''
    
    return payload_is_json, json_payload

# setup the server once
udp_server_socket = init_udp_server()

while(True):
    bytesAddressPair = udp_server_socket.recvfrom(1024)

    message = bytesAddressPair[0]
    address = bytesAddressPair[1]

    print(message) 

    '''
    First, make sure the udp payload is a valid json string.
    If it is, valid_json is set to True and message contains the JSON object.
    If not, valid_json is set to False and message is ''
    '''
    valid_json, client_message = check_valid_json(message)

    # Just in case that slipped, only validate the schema if the message is a valid json
    if (valid_json):
        # OK, so it is JSON. Let's make sure it is semantically valid
        if (validate_json_schema(client_message)):
            print("Valid schema detected!")
        else:
            print("Failed schema validation, skipping.")
