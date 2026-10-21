import socket
import sys
import time
import threading

HEADER = 64
SERVER = "0.0.0.0"
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

def check_engine(conn, addr):
    client_engine = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # El Monitor se conecta como cliente al servidor del Engine
        client_engine.connect(ADDR_WS)
        print(f"[MONITOR] Conectado al servidor del Engine")
        
        while True:
            msg = "Health-Check"
            
            # Envías el mensaje a través del socket de la conexión
            send(msg, client_engine)
            print(f"[MONITOR] Enviado al Engine: {msg}")
            
            # Esperar exactamente 1 segundo antes del siguiente envío
            time.sleep(1.0)
            
    except Exception as e:
        print(f"[MONITOR ERROR] Conexión interrumpida con el Engine: {e}")
        # Si se pierde la conexión, aquí puedes notificar el fallo/fuga a Central
    finally:
        client_engine.close()

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
    
    #Central
    ADDR_CENTRAL = (IP_CENTRAL, PORT_CENTRAL)
    client_central = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_central.connect(ADDR_CENTRAL)
    print (f"Establecida conexión en [{ADDR_CENTRAL}]")
    
    tramaRegistroCentral = (f"REGISTRO#{ID_ESTACION}#{UBICACION}")
    send(tramaRegistroCentral, client_central)
    
    respuestaCentral = client_central.recv(2048).decode(FORMAT)
    print("Recibo de la Central: ", respuestaCentral)
    respuestaEsperada = "STATUS#OK#Estacion registrada correctamente"

    if respuestaCentral.strip() == respuestaEsperada:
        print("Estación registrada en Central.")  
    else:
        print("ERROR al intentar registrar la estación en Central")
        client_central.close()
    
    
    #Engine
    ADDR_WS = ("localhost", PORT_WS)
    client_engine = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_engine.connect(ADDR_WS)
    
    tramaRegistroEngine = (f"REGISTRO#{ID_ESTACION}")
    send(tramaRegistroEngine, client_engine)
    
    respuestaEngine = client_engine.recv(2048).decode(FORMAT)
    print("Recibo del Engine: ", respuestaEngine)
    respuestaEsperada = "STATUS#OK#Estacion conectada a Engine correctamente"
    
    if respuestaEngine.strip() == respuestaEsperada:
        print("Estación conectada con Engine.")  
    else:
        print("ERROR al intentar conectarse a Engine")
        client_engine.close()
    
    """
    #Empezar health-check
    hilo_engine = threading.Thread(target=check_engine, args=("localhost", PORT_WS), daemon=True)
    hilo_engine.start()
    """
else:
    print ("Oops!. Parece que algo falló. Necesito estos argumentos: <PORT_WS> <IP_CENTRAL> <PORT_CENTRAL> <ID_ESTACION> <UBICACION> ")
