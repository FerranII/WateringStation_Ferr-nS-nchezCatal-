import socket
import threading
import json
import time
import sqlite3

from sympy import root
import tkinter as tk
from tkinter import ttk

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 25

STATUS = {
    "AVAILABLE": "#00ff2fcf",
    "WATERING": "#00ff2fcf",
    "LEAK": "#dd1529",
    "OUT_OF_SERVICE": "#ff7300",
    "DISCONNECTED": "#9ca0a3"
}
current_status = {} #ID->llave y STATUS->valor

def cambiar_estado(id, status):
    if status in STATUS:
        current_status[id] = status
    else:
        current_status[id] = "DISCONNECTED"

    current_color = STATUS[current_status[id]]
    print(id + " -> " + current_status[id] + " -> " + current_color)
    return current_status[id], current_color

"""
Metodos para leer,insertar,eliminar de la base de datos    
"""
    
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
                    cambiar_estado(ID_ESTACION, "AVAILABLE")
                else:
                    conn.send("STATUS#ERROR#Trama incorrecta".encode(FORMAT))
            else:
                print(f" He recibido del cliente [{addr}] el mensaje: {msg}")
                conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()
 
 
###################
#Apartado Gráfico->tkinder
###################   
def apartado_grafico():
    root = tk.Tk()
    root.title("WM_Central - Irrigation Monitoring Panel")
    root.geometry("800x500")
    barra_botones = tk.Frame(root, bg="#e0e0e0", bd=2, relief=tk.RAISED)

    #Botones
    barra_botones.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    btn_1 = tk.Button(barra_botones, text="Start watering", bg="#00ff2f")
    btn_1.pack(side=tk.LEFT, padx=5, pady=5)

    btn_2 = tk.Button(barra_botones, text="Block WS", bg="#ff7300")
    btn_2.pack(side=tk.LEFT, padx=5, pady=5)

    btn_3 = tk.Button(barra_botones, text="Activate WS", bg="#00ff2f")
    btn_3.pack(side=tk.LEFT, padx=5, pady=5)

    btn_4 = tk.Button(barra_botones, text="Refresh")
    btn_4.pack(side=tk.LEFT, padx=5, pady=5)
    
    #Menu resumen
    barra_resumen = tk.Frame(root, bg="#ded7d7", bd=2, relief=tk.RAISED)
    barra_resumen.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
    
    txt_resumen1 = tk.Label(barra_resumen, text="SYSTEM SUMMARY", bg="#c34c4c", font=("Arial", 10, "bold"))
    txt_resumen1.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen2 = tk.Label(barra_resumen, text=(f"Available: {MAX_CONEXIONES}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen2.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen3 = tk.Label(barra_resumen, text=(f"Watering: {MAX_CONEXIONES}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen3.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen4 = tk.Label(barra_resumen, text=(f"Leak: {MAX_CONEXIONES}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen4.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen5 = tk.Label(barra_resumen, text=(f"Out of service: {MAX_CONEXIONES}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen5.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen6 = tk.Label(barra_resumen, text=(f"Offline: {MAX_CONEXIONES}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen6.pack(side=tk.TOP, padx=5, pady=5, anchor="w")

    root.mainloop()

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    print(NUMERO_CLIENTES)
    while True:
        conn, addr = server.accept()
        if (NUMERO_CLIENTES <= MAX_CONEXIONES):
            NUMERO_CLIENTES += 1
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"CLIENTES ACTIVOS: {NUMERO_CLIENTES}")
            print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES-NUMERO_CLIENTES)
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

NUMERO_CLIENTES = 0
WATERING = 0
AVAILABLE = 0
LEAK = 0
OUT_OF_SERVICE = 0
OFFLINE = 0
print("[STARTING] Servidor inicializándose...")

hilo_servidor = threading.Thread(target=start, daemon=True)
hilo_servidor.start()

apartado_grafico()


