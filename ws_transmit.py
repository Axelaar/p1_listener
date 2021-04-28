# Python3 module to be called from other scripts.
# This script contains the custom function to send
# data to a websocket server.
# Created November 6, 2020 by Bram Langen.
# Version 2.0 - Tested.

from websocket import create_connection;

############################################################
# Send data as a websocket telegram.
############################################################
def ws_transmit(ws_connection_detail, identifier, data, delimiter):
    'Send the identifier and data as a WebSocket packet'
    try:
        ws = create_connection(ws_connection_detail);
        data = identifier + delimiter + str(data) + delimiter;
        ws.send(data);                                  # write the data to the WebServer
        ws.close();
    except:
        pass

