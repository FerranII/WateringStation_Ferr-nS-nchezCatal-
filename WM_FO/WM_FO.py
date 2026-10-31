import socket
import sys
import threading
import json
import tkinter as tk
from tkinter import ttk

HEADER = 64
FORMAT = 'utf-8'
COLOR_BLANCO = "#ffffff"

def send(msg, client):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def recv_msg(client):
    msg_length = client.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length.strip())
        return client.recv(msg_length).decode(FORMAT)
    return ""
#########Apartado gráfico###############3
def apartado_grafico():
    root = tk.Tk()
    root.title("WM_FO - Irrigation Monitoring Panel")
    root.geometry("800x500")
    
    root.mainloop()
########## MAIN ##########
#Formato: <IP_KAFKA> <PORT_KAFKA> <ID_OPERARIO>
if len(sys.argv) == 4:
    IP_CENTRAL = sys.argv[1]
    PORT_CENTRAL = int(sys.argv[2])
    ID_OPERARIO = sys.argv[3]

    ADDR_CENTRAL = (IP_CENTRAL, PORT_CENTRAL)
    client_central = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_central.connect(ADDR_CENTRAL)
        print(f"[CONECTADO] Conectado a la Central en {ADDR_CENTRAL}")
        
        trama_registro = f"REGISTRO_FO#{ID_OPERARIO}"
        send(trama_registro, client_central)
        
        msg_len = client_central.recv(HEADER).decode(FORMAT)
        if msg_len:
            respuesta = client_central.recv(int(msg_len.strip())).decode(FORMAT)
            print(f"Respuesta Central: {respuesta}")

        hilo_escucha = threading.Thread(target=escuchar_central, args=(client_central,), daemon=True)
        hilo_escucha.start()

        apartado_grafico()
       
    except Exception as e:
        print(f"[ERROR DE CONEXIÓN] No se pudo conectar con la Central: {e}")
    finally:
        client_central.close()
else:
    print("Oops!. Parece que faltan argumentos.")
    print("Uso correcto: python WM_FO.py <IP_CENTRAL> <PORT_CENTRAL> <ID_OPERARIO>")