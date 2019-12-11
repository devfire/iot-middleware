import socket
import sys
import requests
import settings
import os
import validators

def init_udp_server():
    # listen on all interefaces
    HOST = ""

    # port to listen on
    PORT = 3333

    # Datagram (udp) socket
    try:
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        settings.logger.debug("Socket created")
    except OSError as err:
        settings.logger.error(err)
        sys.exit()

    # Bind socket to host and port
    try:
        UDPServerSocket.bind((HOST, PORT))
    except OverflowError as err:
        settings.logger.error(err)	
        sys.exit()

    settings.logger.info("UDP server is ready to go.")

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

    settings.logger.debug("Checking the config file for the pin settings")
    # check to see if there's a relevant section in settings.ini and that section has the pin
    if settings.config.has_option(mac,feed_name):
        # it does, let's grab its pin
        pin = settings.config[mac][feed_name]
        settings.logger.debug("Found valid config for pin " + str(pin))

        # format the URL properly. This is a REST call to blynk.
        URL = BLYNK_URL + '/' + BLYNK_AUTH + '/update/V' + str(pin) + '?value=' + str(value)
        settings.logger.debug("Posting to " + URL)

        # attempt to send data to blynk
        try:    
            response = requests.get(URL)
            settings.logger.debug("Sent data successfully to " + URL)
        except requests.exceptions.RequestException as err:
            settings.logger.error(err)
    else:
        # either mac or the feedname is not found, skipping
        settings.logger.error("Not sure what to do with " + str(feed_name) + " from " + str(mac))

def infinite_loop(udp_server_socket):
    '''
    Let's get the infinite loop going.
    Essentially, udp_server_socket.recvfrom(1024) will block, waiting for a new message.
    Once the message is received, we need to:
    1. make sure it's actually JSON (syntactic validation)
    2. make sure all the required fields are present (semantic validation)
    3. publish to blynk
    4. (optionally) do what else needs to be done
    '''
    settings.logger.debug("Starting the processor main loop.")
    while(True):
        bytesAddressPair = udp_server_socket.recvfrom(1024)

        # this is the actual message
        message = bytesAddressPair[0]

        # source IP addressed, ignored for now
        address = bytesAddressPair[1]

        settings.logger.debug("Received " + str(message) + "from " + str(address))

        '''
        First, make sure the udp payload is a valid json string.
        If it is, valid_json is set to True and message contains the JSON object.
        We do it in one shot since we are much more likely to get valid JSON than not.
        If not, valid_json is set to False and message is an empty string ''.
        '''
        valid_json_bool, current_client_message = validators.validate_json(message)

        # only validate the schema if the message is a valid json
        if (valid_json_bool):
            # OK, so it is JSON. Let's make sure it is semantically valid
            if (validators.validate_json_schema(current_client_message)):
                settings.logger.debug("Valid schema detected!")
            else:
                settings.logger.error("Failed schema validation, skipping.")
                continue # go to the beginning of the while loop
        else:
            settings.logger.error("Could not serialize payload to JSON, skipping.")
            continue # go to the beginning of the while loop
        
        # print the received message for debugging purposes
        settings.logger.debug(current_client_message)
        
        '''
        Publish the data to blynk.
        NOTE: we don't know the correct pin, we'll look it up later
        '''
        send_value_to_blynk(current_client_message)

if __name__ == '__main__':
    validators.validate_env_variables()
    validators.validate_config_file()
    server_socket = init_udp_server()
    infinite_loop(server_socket)