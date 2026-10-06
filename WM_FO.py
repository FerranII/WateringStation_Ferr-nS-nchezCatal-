import socket
import sys

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
FIN = "FIN"

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    
########## MAIN ##########
if  (len(sys.argv) == 5):
    IP_BROKER = sys.argv[1]
    PORT_BROKER = int(sys.argv[2])
    OPERATOR_ID = sys.argv[3]

    ADDR_BROKER = (IP_BROKER, PORT_BROKER)
    msg=sys.argv[3]
    while msg != FIN :
        print("Envio al servidor: ", msg)
        send(msg)
        print("Recibo del Servidor: ", client.recv(2048).decode(FORMAT))
        msg=input()
    print("Cierro conexión")
    send(FIN)
    client.close()
else:
    print ("Oops!. Parece que algo falló. Necesito estos argumentos: <ServerIP> <Puerto> <Estacion> <Ubicacion>")
