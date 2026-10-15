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

ESTADOS_VALIDOS = ["AVAILABLE", "WATERING", "LEAK", "OUT_OF_SERVICE", "OFFLINE"]
STATUS = {
    "AVAILABLE": "#00ff2fcf",
    "WATERING": "#00ff2fcf",
    "LEAK": "#dd1529",
    "OUT_OF_SERVICE": "#ff7300",
    "OFFLINE": "#9ca0a3"
}
def estado_AVAILABLE(i):
    global AVAILABLE
    if(i): AVAILABLE += 1
    else: AVAILABLE -=1
def estado_WATERING(i):
    global WATERING
    if(i): WATERING += 1
    else: WATERING -=1
def estado_LEAK(i):
    global LEAK
    if(i): LEAK += 1
    else: LEAK -=1
def estado_OUT_OF_SERVICE(i):
    global OUT_OF_SERVICE
    if(i): OUT_OF_SERVICE += 1
    else: OUT_OF_SERVICE -=1
def estado_OFFLINE(i):
    global OFFLINE
    if(i): OFFLINE += 1
    else: OFFLINE -=1 
          
#############BASE DATOS###############################    
def obetener_WS(ID):
    try:
        conexion = sqlite3.connect('WS_BaseDatos.db')
        cursor = conexion.cursor()
        cursor.execute("SELECT ID, Ubicacion, Estado, Last_Watering FROM WS WHERE ID = ?", (ID,))
        resultado = cursor.fetchone()
    
        conexion.close()
        return resultado
    except Exception as e:
        print(f"[DB ERROR] No se pudo leer la base de datos: {e}")
        return []

def obtener_todas_WS():
    try:
        conexion = sqlite3.connect('WS_BaseDatos.db')
        cursor = conexion.cursor()
        cursor.execute("SELECT ID, Ubicacion, Estado, Last_Watering FROM WS")
        resultados = cursor.fetchall()
        
        conexion.close()
        return resultados
    except Exception as e:
        print(f"[DB ERROR] No se pudo leer la base de datos: {e}")
        return []

def insertar_WS(ID, Ubicacion):
    try:
        conexion = sqlite3.connect('WS_BaseDatos.db')
        cursor = conexion.cursor()
        cursor.execute("""INSERT OR IGNORE INTO WS (ID, Ubicacion) VALUES (?, ?)""", (ID, Ubicacion))
        
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"[DB ERROR]: {e}")

def actualizar_estado_WS(ID, Estado):
    if Estado not in ESTADOS_VALIDOS: return
    
    funciones_estados = {
        "AVAILABLE": estado_AVAILABLE,
        "WATERING": estado_WATERING,
        "LEAK": estado_LEAK,
        "OUT_OF_SERVICE": estado_OUT_OF_SERVICE,
        "OFFLINE": estado_OFFLINE
    }
    try:
        conexion = sqlite3.connect('WS_BaseDatos.db')
        cursor = conexion.cursor()

        cursor.execute("SELECT Estado FROM WS WHERE ID = ?", (ID,))
        resultado = cursor.fetchone()
        old_estado = resultado[0] if resultado else None
        
        if old_estado in funciones_estados: funciones_estados[old_estado](False)
        funciones_estados[Estado](True)

        cursor.execute("""UPDATE WS SET Estado = ? WHERE ID = ?""", (Estado, ID))
        conexion.commit()
        conexion.close()
        
        print(f"[DB SUCCESS] Estación {ID} actualizada de '{old_estado}' a '{Estado}'.")
    except Exception as e:
        print(f"[DB ERROR] No se pudo resolver el estado: {e}")

###############ATENDER CONEXIONES#######################
def start():
    global NUMERO_CLIENTES
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
            
#############RESPONDER CLIENTES###############################
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
                    insertar_WS(ID_ESTACION, UBICACION)
                    actualizar_estado_WS(ID_ESTACION,"AVAILABLE");
                else:
                    conn.send("STATUS#ERROR#Trama incorrecta".encode(FORMAT))
            else:
                print(f" He recibido del cliente [{addr}] el mensaje: {msg}")
                conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()
####################START IRRIGATION#######################
def check_irrigation():
    return

###########################
#Apartado Gráfico->tkinder
###############################   
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
    txt_resumen2 = tk.Label(barra_resumen, text=(f"Available: {AVAILABLE}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen2.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen3 = tk.Label(barra_resumen, text=(f"Watering: {WATERING}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen3.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen4 = tk.Label(barra_resumen, text=(f"Leak: {LEAK}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen4.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen5 = tk.Label(barra_resumen, text=(f"Out of service: {OUT_OF_SERVICE}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen5.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_resumen6 = tk.Label(barra_resumen, text=(f"Offline: {OFFLINE}"), bg="#ded7d7", font=("Arial", 8))
    txt_resumen6.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    
    #Menu resumen
    barra_leyenda = tk.Frame(root, bg="#ded7d7", bd=2, relief=tk.RAISED)
    barra_leyenda.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    txt_leyenda1 = tk.Label(barra_leyenda, text="Available / Watering", bg="#ded7d7", font=("Arial", 10, "bold"))
    txt_leyenda1.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    cuadro_color1 = tk.Label(barra_leyenda, bg="#00ff2f", width=2, height=1)
    cuadro_color1.pack(side=tk.LEFT, padx=(0, 5), anchor="w")

    root.mainloop()
        
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

estaciones = obtener_todas_WS()
for estacion in estaciones:
    actualizar_estado_WS(estacion[0],"OFFLINE")
    print(f"Estación ID: {estacion[0]}, Ubicación: {estacion[1]}, Estado: {estacion[2]}, Last_time: {estacion[3]}")
OFFLINE = len(estaciones)

hilo_servidor = threading.Thread(target=start, daemon=True)
hilo_servidor.start()
    
apartado_grafico()