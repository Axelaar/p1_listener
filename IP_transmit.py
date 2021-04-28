# Python3 module to be called from other scripts.
# This script contains the custom function to send
# IP telegrams to a server.
# Created November 23, 2020 by Bram Langen.
# Version 1.0 - Initial version.

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
            error_msg = 'Zenden van de actuele gegevens naar de server hervat.';
            UDPSock_error = False;
    except:
        if not UDPSock_error:
            address = addr[0] + ':' + str(addr[1]);
            error_msg = 'Fout bij het zenden van de gegevens naar server %s.' % address;
            UDPSock_error = True;
    return UDPSock_error, error_msg;

