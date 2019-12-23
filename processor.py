import socket
import sys
import requests
import shared
import os
import validators

def init_udp_server():
    """Initialize the UDP server and return the socket"""
    HOST = ""

    """port to listen on"""
    PORT = 3333

    """Datagram (udp) socket creation"""
    try:
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        shared.logger.debug("Socket created")
    except OSError as err:
        shared.logger.error(err)
        sys.exit()

    """Bind socket to host and port"""
    try:
        UDPServerSocket.bind((HOST, PORT))
    except OverflowError as err:
        shared.logger.error(err)	
        sys.exit()

    shared.logger.info("UDP server is ready to go.")

    return UDPServerSocket

def send_value_to_blynk(client_message):
    """Send the values to blynk.io 
    These are the required environment variables that must be set.
    """
    BLYNK_AUTH = os.getenv("BLYNK_AUTH")
    BLYNK_URL = os.getenv("BLYNK_URL")

    """
    Get all the things assigned to the right values:
    - value is the actual numeric value of the sensor
    - mac is the mac address, this is how we figure out what to route where
    - feed name is used to look up the blynk virtual pin
    """
    value = client_message["value"]
    mac   = client_message["mac"]
    feed_name = client_message["feedName"]

    shared.logger.debug("Checking the config file for the pin shared")
    """check to see if there's a relevant section in shared.ini and that section has the pin"""
    if shared.config.has_option(mac,feed_name):
        """it does, let's grab its pin"""
        pin = shared.config[mac][feed_name]
        shared.logger.debug("Found valid config for pin " + str(pin))

        """format the URL properly. This is a REST call to blynk."""
        URL = BLYNK_URL + '/' + BLYNK_AUTH + '/update/V' + str(pin) + '?value=' + str(value)
        shared.logger.debug("Posting to " + URL)

        """attempt to send data to blynk"""
        try:    
            response = requests.get(URL)
            shared.logger.debug("Sent data successfully to " + URL)
        except requests.exceptions.RequestException as err:
            shared.logger.error(err)
    else:
        """either mac or the feedname is not found, skipping"""
        shared.logger.error("Not sure what to do with " + str(feed_name) + " from " + str(mac))

def main(udp_server_socket):
    """
    Get the infinite loop going.
    Essentially, udp_server_socket.recvfrom(1024) will block, waiting for a new message.
    
    Once the message is received, we need to:
    1. make sure it's actually JSON (syntactic validation)
    2. make sure all the required fields are present (semantic validation)
    3. publish to blynk
    4. (optionally) do what else needs to be done
    """
    shared.logger.debug("Starting the processor main loop.")
    while(True):
        bytesAddressPair = udp_server_socket.recvfrom(1024)

        """this is the actual message"""
        message = bytesAddressPair[0]

        """source IP addressed, ignored for now"""
        address = bytesAddressPair[1]

        shared.logger.debug("Received " + str(message) + "from " + str(address))

        """
        First, make sure the udp payload is a valid json string.
        If it is, valid_json is set to True and message contains the JSON object.
        
        We do it in one shot since we are much more likely to get valid JSON than not.
        If not, valid_json is set to False and message is an empty string ''.
        """
        valid_json_bool, current_client_message = validators.validate_json(message)

        """only validate the schema if the message is a valid json"""
        if (valid_json_bool):
            """OK, so it is JSON. Let's make sure it is semantically valid"""
            if (validators.validate_json_schema(current_client_message)):
                shared.logger.debug("Valid schema detected!")
            else:
                shared.logger.error("Failed schema validation, skipping.")
                continue # go to the beginning of the while loop
        else:
            shared.logger.error("Could not serialize payload to JSON, skipping.")
            continue # go to the beginning of the while loop
        
        """print the received message for debugging purposes"""
        shared.logger.debug(current_client_message)
        
        """
        Publish the data to blynk.
        NOTE: we don't know the correct virtual pin, we'll look it up later
        """
        send_value_to_blynk(current_client_message)

if __name__ == '__main__':
    """make sure all of the required env vars are present"""
    validators.validate_env_variables()

    """make sure the config file is present"""
    validators.validate_config_file()

    """initialize the server, get the socket back"""
    server_socket = init_udp_server()

    """start the infinite loop, pass the socket as a parameter"""
    main(server_socket)