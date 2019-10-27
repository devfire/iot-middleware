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
    schema = {
        "type" : "object",
        "properties" : {
            "mac" : {"type" : "string"},
            "feedName" : {"type" : "string"},
            "value" : {"type" : "number"},
        },
    }

    try:
        validate(payload, schema)
        return True
    except jsonschema.exceptions.ValidationError as ve:
        sys.stderr.write(str(ve) + "\n")
        return False


# setup the server once
udp_server_socket = init_udp_server()

while(True):
    
    bytesAddressPair = udp_server_socket.recvfrom(1024)

    message = bytesAddressPair[0]
    address = bytesAddressPair[1]

    client_message = "Message from Client:{}".format(message)
    #clientIP  = "Client IP Address:{}".format(address)

    '''
    try:
        client_message = json.loads(message)
        valid_json = True
    except:
        print("Could not serialize payload to JSON, skipping.")
        valid_json = False
    '''

    valid_json = True

    if (valid_json):
        print(client_message)

        if (validate_json_schema(client_message)):
            print("Valid schema detected!")
        else:
            print("Failed schema validation, skipping.")
