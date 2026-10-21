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
MAX_CONEXIONES = 250
RUTA_BD = 'WS_BaseDatos.db'

#Posicion columna en la BD
POS_ID, POS_LOCATION, POS_STATUS, POS_LASTWATERING = 0,1,2,3

ESTADOS_VALIDOS = ["AVAILABLE", "WATERING", "LEAK", "OUT_OF_SERVICE", "OFFLINE"]
STATUS_COLORS = {
    "AVAILABLE": "#00ff2f",
    "WATERING": "#00ff2f",
    "LEAK": "#dd1529",
    "OUT_OF_SERVICE": "#ff7300",
    "OFFLINE": "#9ca0a3"
}
COLOR_BLANCO = "#ffffff"

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
        conexion = sqlite3.connect(RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT ID, Location, Status, Last_Watering FROM WS WHERE ID = ?", (ID,))
        resultado = cursor.fetchone()
    
        conexion.close()
        return resultado
    except Exception as e:
        print(f"[DB ERROR] No se pudo leer la base de datos: {e}")
        return []

def obtener_todas_WS():
    try:
        conexion = sqlite3.connect(RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT ID, Location, Status, Last_Watering FROM WS ORDER BY ID ASC")
        resultados = cursor.fetchall()
        
        conexion.close()
        return resultados
    except Exception as e:
        print(f"[DB ERROR] No se pudo leer la base de datos: {e}")
        return []

def insertar_WS(ID, Location):
    try:
        conexion = sqlite3.connect(RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("""INSERT OR IGNORE INTO WS (ID, Location) VALUES (?, ?)""", (ID, Location))
        
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"[DB ERROR]: {e}")

def delete_WS(ID):
    try:
        conexion = sqlite3.connect(RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM WS WHERE ID = ?", (ID,))
        
        conexion.commit()
        conexion.close()
        print(f"[DB SUCCESS] Estación {ID} eliminada correctamente.")
    except Exception as e:
        print(f"[DB ERROR]: {e}")

def actualizar_estado_WS(ID, Status):
    if Status not in ESTADOS_VALIDOS: return
    
    funciones_estados = {
        "AVAILABLE": estado_AVAILABLE,
        "WATERING": estado_WATERING,
        "LEAK": estado_LEAK,
        "OUT_OF_SERVICE": estado_OUT_OF_SERVICE,
        "OFFLINE": estado_OFFLINE
    }
    try:
        conexion = sqlite3.connect(RUTA_BD)
        cursor = conexion.cursor()

        cursor.execute("SELECT Status FROM WS WHERE ID = ?", (ID,))
        resultado = cursor.fetchone()
        old_estado = resultado[0] if resultado else None
        
        if old_estado in funciones_estados: funciones_estados[old_estado](False)
        funciones_estados[Status](True)

        cursor.execute("""UPDATE WS SET Status = ? WHERE ID = ?""", (Status, ID))
        conexion.commit()
        conexion.close()
        
        print(f"[DB SUCCESS] Estación {ID} actualizada de '{old_estado}' a '{Status}'.")
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
                    LOCATION = partes[2]
                    print("Recibida la trama del cliente")
                    print("ID_ESTACION -> "+ID_ESTACION)
                    print("Location -> "+LOCATION)
                    conn.send("STATUS#OK#Estacion registrada correctamente".encode(FORMAT))
                    insertar_WS(ID_ESTACION, LOCATION)
                    actualizar_estado_WS(ID_ESTACION,"AVAILABLE");
                else:
                    conn.send("STATUS#ERROR#Trama incorrecta".encode(FORMAT))
            else:
                print(f" He recibido del cliente [{addr}] el mensaje: {msg}")
                conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()
    
####################START IRRIGATION#######################
def check_irrigation(ID):
    datos_ws = obetener_WS(ID)
    if(datos_ws and datos_ws[POS_STATUS] == "AVAILABLE"):
        return True
    return False

###Funcionalidad botones##############
def WS_seleccionada():
    ws = tabla.selection()
    if ws:
        valores = tabla.item(ws[POS_ID], "values")
        return valores[POS_ID]
    
    return None

def quitar_seleccion_fuera(event):
    if event.widget != tabla and event.widget not in (btn_StartWatering,btn_BLOCKWS,btn_ACTIVATEWS, btn_DELETEWS): tabla.selection_remove(tabla.selection())

def btn_watering():
    ws_id = WS_seleccionada()
    if ws_id:
        if(check_irrigation(ws_id)):
            print(f"Iniciando riego para la estación: {ws_id}")
            actualizar_estado_WS(ws_id,"WATERING")
        else:
            print("No pasa los controles")
    else:
        print("No hay estación seleccionada para regar")

def btn_block():
    ws_id = WS_seleccionada()
    print("no implementado")

def btn_activate():
    ws_id = WS_seleccionada()
    print("no implementado")
       
def btn_delete():
    ws_id = WS_seleccionada()
    if ws_id:
        delete_WS(ws_id)
    else:
        print("No hay estación seleccionada para eliminar")
###########################
#Apartado Gráfico->tkinder
###############################

def refrescar_interfaz():
    global WATERING_BLINK 
    id_seleccion = WS_seleccionada()
    item_a_seleccionar = None
            
    #eliminar y insertar
    for row in tabla.get_children():
        tabla.delete(row)
        
    estaciones_actuales = obtener_todas_WS()
    for est in estaciones_actuales:
        estado_actual = est[POS_STATUS]
        
        tag_a_usar = estado_actual
        if estado_actual == "WATERING":
            tag_a_usar = "WATERING_GREEN" if WATERING_BLINK else "WATERING_WHITE"
            
        row_id = tabla.insert("", tk.END, values=est, tags=(tag_a_usar,))
        if id_seleccion and str(est[POS_ID]) == str(id_seleccion): item_a_seleccionar = row_id

    if item_a_seleccionar: # rstaurar selección si existía
        tabla.selection_set(item_a_seleccionar)
        tabla.focus(item_a_seleccionar)
        
    txt_numAvailable.config(text=f"Available: {AVAILABLE}")
    txt_numWatering.config(text=f"Watering: {WATERING}")
    txt_numLeak.config(text=f"Leak: {LEAK}")
    txt_numOutOfService.config(text=f"Out of service: {OUT_OF_SERVICE}")
    txt_numOffline.config(text=f"Offline: {OFFLINE}")
    
    WATERING_BLINK = not WATERING_BLINK 
    root.after(1000, refrescar_interfaz)
    
def apartado_grafico():
    global root, tabla
    global btn_StartWatering, btn_BLOCKWS, btn_ACTIVATEWS, btn_DELETEWS
    global txt_numAvailable, txt_numWatering, txt_numLeak, txt_numOutOfService, txt_numOffline
    
    root = tk.Tk()
    root.title("WM_Central - Irrigation Monitoring Panel")
    root.geometry("800x500")
    barra_botones = tk.Frame(root, bg= COLOR_BLANCO, bd=2, relief=tk.RAISED)

    #Botones
    barra_botones.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    btn_StartWatering = tk.Button(barra_botones, text="Start watering", bg=STATUS_COLORS["AVAILABLE"], command=btn_watering)
    btn_StartWatering.pack(side=tk.LEFT, padx=5, pady=5)

    btn_BLOCKWS = tk.Button(barra_botones, text="Block WS", bg=STATUS_COLORS["LEAK"], command=btn_block)
    btn_BLOCKWS.pack(side=tk.LEFT, padx=5, pady=5)

    btn_ACTIVATEWS = tk.Button(barra_botones, text="Activate WS", bg=STATUS_COLORS["AVAILABLE"], command=btn_activate)
    btn_ACTIVATEWS.pack(side=tk.LEFT, padx=5, pady=5)
    
    btn_DELETEWS = tk.Button(barra_botones, text="Delete WS", bg=STATUS_COLORS["LEAK"], command=btn_delete)
    btn_DELETEWS.pack(side=tk.LEFT, padx=5, pady=5)
    
    # Tabla dinámica
    marco_tabla = tk.Frame(root)
    marco_tabla.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
    columnas = ("ID", "Location", "Status", "Last_Watering")
    tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings")
    
    #Asignamos colores
    for estado, color in STATUS_COLORS.items(): 
        if estado != "WATERING":
            tabla.tag_configure(estado, background=color)
            
    tabla.tag_configure("WATERING_GREEN", background=STATUS_COLORS["AVAILABLE"])
    tabla.tag_configure("WATERING_WHITE", background=COLOR_BLANCO)
    
    tabla.heading("ID", text="ID Station", anchor="w")
    tabla.heading("Location", text="Location", anchor="w")
    tabla.heading("Status", text="Status", anchor="w")
    tabla.heading("Last_Watering", text="Último Riego", anchor="w")
    
    tabla.column("ID", width=100, anchor="w")
    tabla.column("Location", width=250, anchor="w")
    tabla.column("Status", width=150, anchor="w")
    tabla.column("Last_Watering", width=200, anchor="w")
    
    scrollbar = ttk.Scrollbar(marco_tabla, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=scrollbar.set)
    tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Llenar tabla con BD
    estaciones_actuales = obtener_todas_WS()
    for est in estaciones_actuales:
        tabla.insert("", tk.END, values=est)
    
    root.bind("<Button-1>", quitar_seleccion_fuera)
    
    #Menu resumen
    barra_resumen = tk.Frame(root, bg=COLOR_BLANCO, bd=2, relief=tk.RAISED)
    barra_resumen.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
    
    txt_resumen1 = tk.Label(barra_resumen, text="SYSTEM SUMMARY", bg=STATUS_COLORS["LEAK"], font=("Arial", 10, "bold"))
    txt_resumen1.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numAvailable = tk.Label(barra_resumen, text=(f"Available: {AVAILABLE}"), bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numAvailable.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numWatering = tk.Label(barra_resumen, text=(f"Watering: {WATERING}"), bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numWatering.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numLeak = tk.Label(barra_resumen, text=(f"Leak: {LEAK}"), bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numLeak.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numOutOfService = tk.Label(barra_resumen, text=(f"Out of service: {OUT_OF_SERVICE}"), bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numOutOfService.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numOffline = tk.Label(barra_resumen, text=(f"Offline: {OFFLINE}"), bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numOffline.pack(side=tk.TOP, padx=5, pady=5, anchor="w")

    refrescar_interfaz()
    
    root.mainloop()
        
######################### MAIN ##########################
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

NUMERO_CLIENTES = 0
WATERING, AVAILABLE, LEAK, OUT_OF_SERVICE, OFFLINE = 0, 0, 0, 0, 0
WATERING_BLINK = True

print("[STARTING] Servidor inicializándose...")

estaciones = obtener_todas_WS()
for estacion in estaciones:
    actualizar_estado_WS(estacion[POS_ID],"OFFLINE")
    print(f"Estación ID: {estacion[POS_ID]}, Ubicación: {estacion[POS_LOCATION]}, Status: {estacion[POS_STATUS]}, Last_time: {estacion[POS_LASTWATERING]}")
OFFLINE = len(estaciones)
WATERING, AVAILABLE, LEAK, OUT_OF_SERVICE = 0, 0, 0, 0

hilo_servidor = threading.Thread(target=start, daemon=True)
hilo_servidor.start()
    
apartado_grafico()