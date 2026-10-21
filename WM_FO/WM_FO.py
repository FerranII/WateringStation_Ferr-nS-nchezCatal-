import socket
import sys

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
FIN = "FIN"

def send(msg, client):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    
########## MAIN ##########
#Explicación:
#Formato: <IP_CENTRAL> <PORT_CENTRAL> <ID_WS>
if  (len(sys.argv) == 4):
    IP_CENTRAL = sys.argv[1]
    PORT_CENTRAL = int(sys.argv[2])
    ID_WS = sys.argv[3]
