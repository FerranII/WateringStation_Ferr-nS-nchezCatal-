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

def check_engine(client_engine, client_central):
    try:
        while True:
            msg = "Health-Check"
            
            send(msg, client_engine)
            print(f"[MONITOR] Enviado al Engine: {msg}")
            msg_length = client_engine.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length.strip())
                msg_engine = client_engine.recv(msg_length).decode(FORMAT)
                print(f"[MONITOR] Datos recibidos del Engine: {msg_engine}")
                
                trama_Health_Central = None
                partes = msg_engine.split("#")
                if "HEALTH_UPDATE" in msg_engine:
                    datos_engine = "#".join(partes[1:])
                    trama_Health_Central = f"STATUS_ENGINE#{ID_ESTACION}#{datos_engine}"
                
                send(trama_Health_Central, client_central)
            time.sleep(1.0)
            
    except Exception as e:
        print(f"[MONITOR ERROR] Conexión interrumpida con el Engine o Central: {e}")
        try:
            trama_Averia_Central = f"STATUS_ENGINE#{ID_ESTACION}#LEAK"
            send(trama_Averia_Central, client_central)
        except:
            pass
            
    finally:
        client_engine.close()

def handle_central(client_engine, client_central):
    try:
        while True:
            msg_length = client_central.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length.strip())
                msg_central = client_central.recv(msg_length).decode(FORMAT)
                
                if "SOLENOID" in msg_central:
                    print("recibido desde central")
                    send(msg_central, client_engine)
    except Exception as e:
        print(f"[MONITOR] Conexión cerrada con la Central: {e}")
    
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
    
    hilo_engine = threading.Thread(target=check_engine, args=(client_engine, client_central), daemon=True)
    hilo_engine.start()
    hilo_central = threading.Thread(target=handle_central, args=(client_engine, client_central), daemon=True)
    hilo_central.start()
    
    try:
        while True:
            tecla = input()
            if tecla.strip().lower() == 'k': break
    except Exception as e:
        print(f"[MONITOR] Error en la entrada: {e}")
    finally:
        client_central.close()
        client_engine.close()
else:
    print ("Oops!. Parece que algo falló. Necesito estos argumentos: <PORT_WS> <IP_CENTRAL> <PORT_CENTRAL> <ID_ESTACION> <UBICACION> ")
