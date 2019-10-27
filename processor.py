import socket
import sys
from jsonschema import validate

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

def validate_json(payload):
    return True


while(True):

    udp_server_socket = init_udp_server()
    bytesAddressPair = udp_server_socket.recvfrom(1024)

    message = bytesAddressPair[0]
    address = bytesAddressPair[1]

    client_message = "Message from Client:{}".format(message)
    clientIP  = "Client IP Address:{}".format(address)
    
    print(client_message)

    validate_json(client_message)
