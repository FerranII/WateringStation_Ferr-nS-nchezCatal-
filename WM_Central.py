import socket 
import threading


HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 2

def handle_client(conn, addr):
    print(f"[NUEVA CONEXION] {addr} connected.")

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
                if(len(partes) == 3):
                    ID_ESTACION = partes[1]
                    UBICACION = partes[2]
                    print("Recibida la trama del cliente")
                    print("ID_ESTACION -> "+ID_ESTACION)
                    print("UBICACION -> "+UBICACION)
                    conn.send("STATUS#OK#Estacion registrada correctamente".encode(FORMAT))
                else:
                    conn.send("STATUS#ERROR#Trama incorrecta".encode(FORMAT))
            else:
                print(f" He recibido del cliente [{addr}] el mensaje: {msg}")
                conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    CONEX_ACTIVAS = threading.active_count()-1
    print(CONEX_ACTIVAS)
    while True:
        conn, addr = server.accept()
        CONEX_ACTIVAS = threading.active_count()
        if (CONEX_ACTIVAS <= MAX_CONEXIONES): 
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")
            print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES-CONEX_ACTIVAS)
        else:
            print("OOppsss... DEMASIADAS CONEXIONES.")
            aviso = "OOppsss... DEMASIADAS CONEXIONES."
            msg_bytes = aviso.encode(FORMAT)
            send_length = str(len(msg_bytes)).encode(FORMAT)
            send_length += b' ' * (HEADER - len(send_length))
            conn.send(send_length)
            conn.send(msg_bytes)
            conn.close()
        
######################### MAIN ##########################
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()

