import socket
import threading
import json
import tkinter as tk
from tkinter import ttk

SERVER_IP = "junction.proxy.rlwy.net"
PORT = 13363
ADDR = (SERVER_IP, PORT)
FORMAT = 'utf-8'
HEADER = 64
FIN = "FIN"

POS_ID, POS_LOCATION, POS_VOLUME, POS_STATUS = 0, 1, 2, 3
STATUS_COLORS = {
    "AVAILABLE": "#00ff2f",
    "WATERING": "#00ff2f",
    "LEAK": "#dd1529",
    "OUT_OF_SERVICE": "#ff7300",
    "OFFLINE": "#9ca0a3"
}
COLOR_BLANCO = "#ffffff"

WATERING, AVAILABLE, LEAK, OUT_OF_SERVICE, OFFLINE = 0, 0, 0, 0, 0
WATERING_BLINK = True

client_socket = None

def conectar_servidor():
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(4.0)
        client_socket.connect(ADDR)
        client_socket.settimeout(None)
        print(f"[CONECTADO] Conectado exitosamente al servidor en {SERVER_IP}:{PORT}")
        return True
    except Exception as e:
        print(f"[ERROR DE CONEXIÓN] El servidor en Railway está apagado o inaccesible: {e}")
        client_socket = None
        return False

def send(msg):
    if not client_socket:
        print("[ERROR] No hay conexión activa con el servidor.")
        return
    try:
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client_socket.send(send_length)
        client_socket.send(message)
    except Exception as e:
        print(f"[ERROR] Fallo al enviar mensaje: {e}")

def recibir_msg(sock):
    header_data = sock.recv(HEADER)
    if not header_data:
        return None
    msg_length = int(header_data.decode(FORMAT).strip())
    
    data = b""
    while len(data) < msg_length:
        packet = sock.recv(msg_length - len(data))
        if not packet:
            break
        data += packet
    return data.decode(FORMAT)

def pedir_datos():
    if not client_socket:
        return None
    try:
        send("GET_ALL_WS")
        json_str = recibir_msg(client_socket)
        if json_str:
            return json.loads(json_str)
    except Exception as e:
        print(f"[ERROR al obtener datos] {e}")
    return None

def WS_seleccionada():
    ws = tabla.selection()
    if ws:
        valores = tabla.item(ws[0], "values")
        return valores[POS_ID]
    return None

def quitar_seleccion(event):
    if event.widget != tabla and event.widget not in (btn_StartWatering, btn_BLOCKWS, btn_ACTIVATEWS, btn_DELETEWS):
        tabla.selection_remove(tabla.selection())

def btn_watering():
    ws_id = WS_seleccionada()
    if ws_id:
        send(f"SOLENOID#{ws_id}#OPEN")
    else:
        print("No hay estación seleccionada")
def btn_block():
    ws_id = WS_seleccionada()
    if ws_id:
        send(f"SOLENOID#{ws_id}#CLOSE")
    else:
        print("No hay estación seleccionada")
def btn_activate():
    ws_id = WS_seleccionada()
    if ws_id:
        send(f"ACTIVATE#{ws_id}")
    else:
        print("No hay estación seleccionada")      
def btn_delete():
    ws_id = WS_seleccionada()
    if ws_id:
        send(f"DELETE#{ws_id}")
    else:
        print("No hay estación seleccionada")

####### Tkinter ###################
def refrescar_interfaz():
    global WATERING_BLINK 
    
    id_seleccion = WS_seleccionada()
    item_a_seleccionar = None
            
    datos_sistema = pedir_datos()
    
    if datos_sistema:
        for row in tabla.get_children():
            tabla.delete(row)
            
        estaciones_actuales = datos_sistema.get("estaciones", [])
        for est in estaciones_actuales:
            estado_actual = est[POS_STATUS]
            tag_a_usar = estado_actual
            if estado_actual == "WATERING":
                tag_a_usar = "WATERING_GREEN" if WATERING_BLINK else "WATERING_WHITE"
                
            row_id = tabla.insert("", tk.END, values=est, tags=(tag_a_usar,))
            if id_seleccion and str(est[POS_ID]) == str(id_seleccion): 
                item_a_seleccionar = row_id

        if item_a_seleccionar: 
            tabla.selection_set(item_a_seleccionar)
            tabla.focus(item_a_seleccionar)
            
        txt_numAvailable.config(text=f"Available: {datos_sistema.get('AVAILABLE', 0)}")
        txt_numWatering.config(text=f"Watering: {datos_sistema.get('WATERING', 0)}")
        txt_numLeak.config(text=f"Leak: {datos_sistema.get('LEAK', 0)}")
        txt_numOutOfService.config(text=f"Out of service: {datos_sistema.get('OUT_OF_SERVICE', 0)}")
        txt_numOffline.config(text=f"Offline: {datos_sistema.get('OFFLINE', 0)}")
    
    WATERING_BLINK = not WATERING_BLINK 
    root.after(1000, refrescar_interfaz)
    
def apartado_grafico():
    global root, tabla
    global btn_StartWatering, btn_BLOCKWS, btn_ACTIVATEWS, btn_DELETEWS
    global txt_numAvailable, txt_numWatering, txt_numLeak, txt_numOutOfService, txt_numOffline
    
    root = tk.Tk()
    root.title("WM_Central (Local Panel) - Irrigation Monitoring Panel")
    root.geometry("800x500")
    barra_botones = tk.Frame(root, bg=COLOR_BLANCO, bd=2, relief=tk.RAISED)

    barra_botones.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    btn_StartWatering = tk.Button(barra_botones, text="Start watering", bg=STATUS_COLORS["AVAILABLE"], command=btn_watering)
    btn_StartWatering.pack(side=tk.LEFT, padx=5, pady=5)

    btn_BLOCKWS = tk.Button(barra_botones, text="Block WS", bg=STATUS_COLORS["LEAK"], command=btn_block)
    btn_BLOCKWS.pack(side=tk.LEFT, padx=5, pady=5)

    btn_ACTIVATEWS = tk.Button(barra_botones, text="Activate WS", bg=STATUS_COLORS["AVAILABLE"], command=btn_activate)
    btn_ACTIVATEWS.pack(side=tk.LEFT, padx=5, pady=5)
    
    btn_DELETEWS = tk.Button(barra_botones, text="Delete WS", bg=STATUS_COLORS["LEAK"], command=btn_delete)
    btn_DELETEWS.pack(side=tk.LEFT, padx=5, pady=5)
    
    marco_tabla = tk.Frame(root)
    marco_tabla.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
    columnas = ("ID", "Location", "Volume", "Status")
    tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings")
    
    for estado, color in STATUS_COLORS.items(): 
        if estado != "WATERING":
            tabla.tag_configure(estado, background=color)
            
    tabla.tag_configure("WATERING_GREEN", background=STATUS_COLORS["AVAILABLE"])
    tabla.tag_configure("WATERING_WHITE", background=COLOR_BLANCO)
    
    tabla.heading("ID", text="ID Station", anchor="w")
    tabla.heading("Location", text="Location", anchor="w")
    tabla.heading("Volume", text="Accumulated Volume", anchor="w")
    tabla.heading("Status", text="Status", anchor="w")
    
    tabla.column("ID", width=100, anchor="w")
    tabla.column("Location", width=250, anchor="w")
    tabla.column("Volume", width=200, anchor="w")
    tabla.column("Status", width=150, anchor="w")
    
    scrollbar = ttk.Scrollbar(marco_tabla, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=scrollbar.set)
    tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    root.bind("<Button-1>", quitar_seleccion)
    
    barra_resumen = tk.Frame(root, bg=COLOR_BLANCO, bd=2, relief=tk.RAISED)
    barra_resumen.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
    
    txt_resumen1 = tk.Label(barra_resumen, text="SYSTEM SUMMARY", bg=STATUS_COLORS["LEAK"], font=("Arial", 10, "bold"))
    txt_resumen1.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numAvailable = tk.Label(barra_resumen, text=f"Available: {AVAILABLE}", bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numAvailable.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numWatering = tk.Label(barra_resumen, text=f"Watering: {WATERING}", bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numWatering.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numLeak = tk.Label(barra_resumen, text=f"Leak: {LEAK}", bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numLeak.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numOutOfService = tk.Label(barra_resumen, text=f"Out of service: {OUT_OF_SERVICE}", bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numOutOfService.pack(side=tk.TOP, padx=5, pady=5, anchor="w")
    txt_numOffline = tk.Label(barra_resumen, text=f"Offline: {OFFLINE}", bg=COLOR_BLANCO, font=("Arial", 8))
    txt_numOffline.pack(side=tk.TOP, padx=5, pady=5, anchor="w")

    refrescar_interfaz()
    root.mainloop()

if __name__ == "__main__":
    print("Iniciando Grafico Central")
    if conectar_servidor():
        apartado_grafico()
    else:
        print("[AVISO] No se pudo abrir la interfaz porque el servidor en Railway está apagado.")