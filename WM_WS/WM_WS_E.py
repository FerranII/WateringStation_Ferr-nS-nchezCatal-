import socket
import sys
import threading

HEADER = 64
PORT = 6000
SERVER = "0.0.0.0"
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_ACTIVAS = 1

VALORES_HEALTH = ("OK", "KO")
def send(msg, client):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    
def health_check(msg): #devuelve los datos de la engine
    global flow_meter, accum_Vol, solenoid_valve, health_engine
    
    if(msg != "Health-Check"): return None
    if(health_engine not in VALORES_HEALTH):
        print("Valor incorrecto health engine")
        return None
    if(flow_meter < 0 or accum_Vol < 0):
        print("Valores no pueden ser negativos")
        return None
    
    if(solenoid_valve):
        accum_Vol += flow_meter/60
            
    return f"HEALTH_UPDATE#{health_engine}#{flow_meter}#{accum_Vol}#{solenoid_valve}"
        
def handle_client(conn, addr):
    global flow_meter, accum_Vol, solenoid_valve, health_engine
    print(f"[NUEVA CONEXIÓN] Conectado desde {addr}")
  
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == FIN:
                connected = False
            elif "REGISTRO" in msg:
                partes = msg.split('#')
                if(len(partes) == 2):
                    ID_ESTACION = partes[1]
                    print("Recibida la trama del cliente")
                    print("ID_ESTACION -> "+ID_ESTACION)
                    conn.send("STATUS#OK#Estacion conectada a Engine correctamente".encode(FORMAT))
                continue    
                    
            elif msg == "Health-Check":
                print("Recibido Health-msg")
                trama_salud = health_check(msg)
                if trama_salud:
                    send(trama_salud, conn)
                else:
                    send("HEALTH_UPDATE#KO#0.0#0.0#False", conn)
                continue
            
            elif "SOLENOID" in msg:
                if "OPEN" in msg:
                    print("opened solenoid")
                    solenoid_valve = True
                else:
                    print("closed solenoid") 
                    solenoid_valve = False
                continue
            
            print(f" He recibido del cliente [{addr}] el mensaje: {msg}")
            conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()

def start():
  server.listen()
  print(f"[LISTENING] Servidor a la escucha en {SERVER}:{PORT_MONITOR}")
  
  while True:
    conn, addr = server.accept()
    numero_conexiones = threading.active_count()-1

    if numero_conexiones <= MAX_ACTIVAS:
      thread = threading.Thread(target=handle_client, args=(conn, addr))
      thread.start()
    else:
      print("ERROR: Solo se debe conectar el monitor correspondiente.")
      conn.send("ERROR: Solo se debe conectar el monitor correspondiente.".encode(FORMAT))
      conn.close()
    
########## MAIN ##########
#Engine: Module that receives information from the flow meter and activates the solenoid valve.
#Formato: <IP_Queue> <PORT_Queue> <PORT_Monitor> <Flow_meter>
if  (len(sys.argv) == 5):
    IP_QUEUE = sys.argv[1]
    PORT_QUEUE = int(sys.argv[2])
    PORT_MONITOR = int(sys.argv[3])
    
    flow_meter = float(sys.argv[4])

    #ADDR_QUEUE = (IP_QUEUE, PORT_QUEUE)
    ADDR_MONITOR = (SERVER, PORT_MONITOR)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR_MONITOR)
    print("Servidor inicializándose para monitor")
    
    accum_Vol = 0.0
    solenoid_valve = False #If false->closed, true->opened
    health_engine = "OK"
    start()    

else:
    print ("Oops!. Parece que algo falló. Necesito estos argumentos: <IP_Queue> <PORT_Queue> <PORT_Monitor> ")