import settings
import socket
import sys
import json
import requests
import validation

def init_udp_server():
    # all interefaces
    HOST = ""

    # port to listen on
    PORT = 3333

    # Datagram (udp) socket
    try:
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        settings.logging.info("Socket created")
    except OSError as err:
        settings.logging.error("OS error: {0}".format(err))
        sys.exit()

    # Bind socket to host and port
    try:
        UDPServerSocket.bind((HOST, PORT))
    except OSError as err:
        settings.logging.error("OS error: {0}".format(err))	
        sys.exit()

    settings.logging.info("UDP server is ready to go.")

    return UDPServerSocket

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

    # check to see if there's a relevant section in settings.ini and that section has the pin
    if settings.config.has_option(mac,feed_name):
        # it does, let's grab its pin
        pin = settings.config[mac][feed_name]

        # format the URL properly. This is a REST call to blynk.
        URL = BLYNK_URL + '/' + BLYNK_AUTH + '/update/V' + str(pin) + '?value=' + str(value)
        settings.logging.info("Sending " + URL)

        # attempt to send data to blynk
        try:    
            response = requests.get(URL)
        except requests.exceptions.RequestException as e:
            settings.logging.error(e)
    else:
        # either mac or the feedname is not found, skipping
        settings.logging.error("Not sure what to do with " + str(feed_name) + " from " + str(mac))

# initialize the logger
settings.logging.basicConfig(level=settings.LOG_LEVEL)

# make sure all of the necessary env variables are defined
validation.validate_settings()

# make sure the settings file actually exists
try:
    settings.config.read_file(open(settings.CONFIG_FILE))
except FileNotFoundError:
    settings.logging.error("Missing config file, exiting.")
    sys.exit(1)

# setup the server once
udp_server_socket = init_udp_server()

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
    valid_json_bool, current_client_message = validation.is_valid_json(message)

    # only validate the schema if the message is a valid json
    if (valid_json_bool):
        # OK, so it is JSON. Let's make sure it is semantically valid
        if (validation.validate_json_schema(current_client_message)):
            settings.logging.info("Valid schema detected!")
        else:
            settings.logging.error("Failed schema validation, skipping.")
            continue # go to the beginning of the while loop
    else:
        settings.logging.error("Could not serialize payload to JSON, skipping.")
        continue # go to the beginning of the while loop
    
    # print the received message for debugging purposes
    settings.logging.debug(current_client_message)
    
    '''
    Publish the data to blynk.
    NOTE: we don't know the correct pin, we'll look it up later
    '''
    send_value_to_blynk(current_client_message)
