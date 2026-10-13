import socket
import sys
import threading

HEADER = 64
FORMAT = 'utf-8'
FIN = "FIN"
INIT = "INIT"
MAX_ACTIVAS = 10

def handle_client(conn, addr):
    print(f"[NUEVA CONEXIÓN] Conectado desde {addr}")
  
    connected = True
    while connected:
          msg_length = conn.recv(HEADER).decode(FORMAT)
          if msg_length:
              msg_length = int(msg_length)
              msg = conn.recv(msg_length).decode(FORMAT)
              if msg == INIT:
                global ID
                ID = conn.recv(msg_length).decode(FORMAT)
              if msg == FIN:
                  connected = False
              print(f" He recibido del cliente [{addr}] el mensaje: {msg}")
              conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()

def start():
  server.listen()
  print(f"[LISTENING] Servidor a la escucha en {IP_SERVER}:{PORT_SERVER}")
  
  while True:
    conn, addr = server.accept()
    numero_conexiones = threading.active_count()-1

    if numero_conexiones <= MAX_ACTIVAS:
      thread = threading.Thread(target=handle_client, args=(conn, addr))
      thread.start()
      print(f"[CONEXIONES ACTIVAS] {numero_conexiones}")
      print(f"CONEXIONES RESTANTES: {MAX_ACTIVAS - numero_conexiones}")
    else:
      print("OOppsss... DEMASIADAS CONEXIONES. ESPERANDO A QUE ALGUIEN SE VAYA")
      conn.send("OOppsss... Demasiadas conexiones. Espera a que alguien se vaya.".encode(FORMAT))
      conn.close()
    
########## MAIN ##########
#Engine: Module that receives information from the flow meter and activates the solenoid valve. 
if  (len(sys.argv) == 5):
    IP_SERVER = sys.argv[1]
    PORT_SERVER = int(sys.argv[2])
    IP_MONITOR = sys.argv[3]
    PORT_MONITOR = int(sys.argv[4])

    ADDR_SERVER = (IP_SERVER, PORT_SERVER)
    ADDR_MONITOR = (IP_MONITOR, PORT_MONITOR)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR_SERVER)
    print("[STARTING] Servidor inicializándose...")
    
    flow_meter = 0.0
    leak_detector = False
    solenoid_valve_evaluator = False
        
    start()    
