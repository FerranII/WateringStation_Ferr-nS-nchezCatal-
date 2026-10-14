import socket
import sys
import threading

HEADER = 64
FORMAT = 'utf-8'
FIN = "FIN"
INIT = "INIT"

def send(msg, client):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    
########## MAIN ##########
#Monitor: Module that monitors the health of the entire system and reports any fault (leak) to CENTRAL. It is also used to authenticate and register the WS with 
#the central system when appropriate. 
#Formato: <PORT_WS> <IP_CENTRAL> <PORT_CENTRAL> <ID_ESTACION> <UBICACION> 
if  (len(sys.argv) == 6):
    PORT_WS = int(sys.argv[1])
    IP_CENTRAL = sys.argv[2]
    PORT_CENTRAL = int(sys.argv[3])
    ID_ESTACION = sys.argv[4]
    UBICACION = sys.argv[5]
    
    ADDR_CENTRAL = (IP_CENTRAL, PORT_CENTRAL)
    client_central = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_central.connect(ADDR_CENTRAL)
    print (f"Establecida conexión en [{ADDR_CENTRAL}]")
    
    tramaRegistro = (f"REGISTRO#{ID_ESTACION}#{UBICACION}")
    send(tramaRegistro, client_central)
    repuestaEsperada = "STATUS#OK#Estacion registrada correctamente"
    
    respuesta = client_central.recv(2048).decode(FORMAT)
    print("Recibo del Servidor: ", respuesta)

    respuestaEsperada = "STATUS#OK#Estacion registrada correctamente"
    if respuesta.strip() == respuestaEsperada:
        print("Estación registrada en Central.")  
    else:
        print("ERROR al intenrar registrar la estación en Central")
        client_central.close()
            
    ADDR_WS = ("localhost", PORT_WS)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR_WS)
    print (f"Establecida conexión WS")
    msg = input()
    while msg != FIN:
        print("Envio al servidor: ", msg)
        send(msg, client_central)
        print("Recibo del Servidor: ", client_central.recv(2048).decode(FORMAT))
        msg=input()
        
        
    """
    client_engine.settimeout(1.0)

try:
    while True:
        # El Monitor pregunta o envía health-check al Engine cada segundo
        time.sleep(1)
        try:
            client_engine.send("CHECK_STATUS".encode('utf-8'))
            respuesta = client_engine.recv(1024).decode('utf-8')
            
            if "KO" in respuesta:
                print("[ALERTA] El Engine reportó KO. Avisando a Central...")
                # Enviar mensaje de fuga a WM_Central aquí
                break
        except socket.timeout:
            print("[ALERTA] El Engine no respondió a tiempo (Timeout). Posible fallo.")
            # Enviar mensaje de fuga a WM_Central aquí
            break
except KeyboardInterrupt:
    print("Monitor cerrado.")
finally:
    client_engine.close()
    """
    
else:
    print ("Oops!. Parece que algo falló. Necesito estos argumentos: <PORT_WS> <IP_CENTRAL> <PORT_CENTRAL> <ID_ESTACION> <UBICACION> ")
