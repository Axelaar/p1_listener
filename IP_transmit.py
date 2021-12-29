# Python3 module to be called from other scripts.
# This script contains the custom function to send
# IP telegrams to a server.
# Created November 23, 2020 by Bram Langen.
# Version 1.01 - Changed message text to English and used the new formatting method.

from socket import socket, AF_INET, SOCK_DGRAM;

UDPSock = socket(AF_INET, SOCK_DGRAM);

############################################################
# Send data as an IP telegram to the specified address.
############################################################
def IP_transmit(addr, data, UDPSock_error):
    'Send the data to the specified server address'
    error_msg = '';
    try:
        UDPSock.sendto(str.encode(data), addr)
        if UDPSock_error:
            error_msg = 'Sending of actuals data resumed.';
            UDPSock_error = False;
    except:
        if not UDPSock_error:
            error_msg = f'Error sending data to server {addr[0]}:{str(addr[1])}.';
            UDPSock_error = True;
    return UDPSock_error, error_msg;

