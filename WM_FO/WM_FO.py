import socket
import sys
import threading

HEADER = 64
FORMAT = 'utf-8'

def send(msg, client):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def escuchar_central(client):
    try:
        while True:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length.strip())
                mensaje = client.recv(msg_length).decode(FORMAT)
                print(f"\n[AVISO DE CENTRAL] {mensaje}\n> ", end="")
    except Exception as e:
        print(f"\n[ERROR] Se ha perdido la conexión con la Central: {e}")
    finally:
        client.close()

########## MAIN ##########
#Módulo para que el operario controle las estaciones y solicite riegos.
#Formato: <IP_CENTRAL> <PORT_CENTRAL> <ID_OPERARIO>
if len(sys.argv) == 4:
    IP_CENTRAL = sys.argv[1]
    PORT_CENTRAL = int(sys.argv[2])
    ID_OPERARIO = sys.argv[3]

    ADDR_CENTRAL = (IP_CENTRAL, PORT_CENTRAL)
    client_central = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_central.connect(ADDR_CENTRAL)
        print(f"[CONECTADO] Conectado a la Central en {ADDR_CENTRAL}")
        
        # Envío de trama de registro/autenticación del Operario
        trama_registro = f"REGISTRO_FO#{ID_OPERARIO}"
        send(trama_registro, client_central)
        
        # Respuesta del registro
        msg_len = client_central.recv(HEADER).decode(FORMAT)
        if msg_len:
            respuesta = client_central.recv(int(msg_len.strip())).decode(FORMAT)
            print(f"Respuesta Central: {respuesta}")

        # Hilo para escuchar mensajes asíncronos de la Central
        hilo_escucha = threading.Thread(target=escuchar_central, args=(client_central,), daemon=True)
        hilo_escucha.start()

        print("\n--- MENÚ FIELD OPERATOR ---")
        print("1. Listar / Ver estaciones disponibles")
        print("2. Solicitar Riego (Ej: RIEGO#ID_ESTACION#OPEN / CLOSE)")
        print("3. Salir")

        while True:
            opcion = input("> ").strip()
            
            if opcion == "1":
                # Solicitar estado/listado de estaciones a la central
                send("LIST_WS", client_central)
                
            elif opcion.startswith("RIEGO#"):
                # Formato esperado: RIEGO#<ID_ESTACION>#OPEN (o CLOSE)
                send(opcion, client_central)
                print("Solicitud de riego enviada a la Central.")
                
            elif opcion.lower() == "salir":
                print("Desconectando operario...")
                break
            else:
                print("Opción no válida. Usa el formato: RIEGO#<ID_ESTACION>#OPEN o '1' para listar.")

    except Exception as e:
        print(f"[ERROR DE CONEXIÓN] No se pudo conectar con la Central: {e}")
    finally:
        client_central.close()
else:
    print("Oops!. Parece que faltan argumentos.")
    print("Uso correcto: python WM_FO.py <IP_CENTRAL> <PORT_CENTRAL> <ID_OPERARIO>")