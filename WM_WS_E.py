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

def handle_client(conn, addr):
    print(f"[NUEVA CONEXIÓN] Conectado desde {addr}")
  
    connected = True
    while connected:
          msg_length = conn.recv(HEADER).decode(FORMAT)
          if msg_length:
              msg_length = int(msg_length)
              msg = conn.recv(msg_length).decode(FORMAT)
              if msg == FIN:
                  connected = False
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
      print(f"CONEXIONES ACTIVAS: {numero_conexiones}")
      print(f"CONEXIONES RESTANTES: {MAX_ACTIVAS - numero_conexiones}")
    else:
      print("ERROR: Solo se debe conectar el monitor correspondiente.")
      conn.send("ERROR: Solo se debe conectar el monitor correspondiente.".encode(FORMAT))
      conn.close()
    
########## MAIN ##########
#Engine: Module that receives information from the flow meter and activates the solenoid valve.
#Formato: <IP_Queue> <PORT_Queue> <PORT_Monitor>
if  (len(sys.argv) == 4):
    IP_QUEUE = sys.argv[1]
    PORT_QUEUE = int(sys.argv[2])
    PORT_MONITOR = int(sys.argv[3])

    #ADDR_QUEUE = (IP_QUEUE, PORT_QUEUE)
    ADDR_MONITOR = (SERVER, PORT_MONITOR)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR_MONITOR)
    print("Servidor inicializándose para monitor")
    
    flow_meter = 0.0
    leak_detector = False
    solenoid_valve_evaluator = False
        
    start()    

else:
    print ("Oops!. Parece que algo falló. Necesito estos argumentos: <IP_Queue> <PORT_Queue> <PORT_Monitor> ")