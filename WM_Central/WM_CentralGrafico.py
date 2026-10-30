import socket
import threading
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

# Conexión global con el servidor central
client_socket = None

def conectar_servidor():
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        print(f"[CONECTADO] Conectado exitosamente al servidor en {SERVER_IP}:{PORT}")
    except Exception as e:
        print(f"[ERROR DE CONEXIÓN] No se pudo conectar al servidor: {e}")

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
        print(f"Enviando comando START WATERING para la estación {ws_id}")
    else:
        print("No hay estación seleccionada para regar")
def btn_block():
    ws_id = WS_seleccionada()
    if ws_id:
        send(f"SOLENOID#{ws_id}#CLOSE")
        print(f"Enviando comando BLOCK para la estación {ws_id}")
    else:
        print("No hay estación seleccionada")
def btn_activate():
    ws_id = WS_seleccionada()
    if ws_id:
        send(f"ACTIVATE#{ws_id}")
        print(f"Enviando comando ACTIVATE para la estación {ws_id}")
    else:
        print("No hay estación seleccionada")            
        
def btn_delete():
    ws_id = WS_seleccionada()
    if ws_id:
        send(f"DELETE#{ws_id}")
        print(f"Enviando comando DELETE para la estación {ws_id}")
    else:
        print("No hay estación seleccionada")

#######TKinder###################
def refrescar_interfaz():
    global WATERING_BLINK 
    
    # Aquí puedes añadir la lógica para pedir datos actualizados al servidor 
    # o refrescar la vista visual de la tabla localmente.
    
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

    # Botones
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
    columnas = ("ID", "Location", "Volume", "Status")
    tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings")
    
    # Asignamos colores
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
    
    # Menú resumen
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
    print("Inicio")
    conectar_servidor()
    apartado_grafico()