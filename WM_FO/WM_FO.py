import socket
import sys
import threading
import json
import queue
import time
import tkinter as tk
from tkinter import ttk, messagebox

HEADER = 64
FORMAT = 'utf-8'
FIN = "FIN"
COLOR_BLANCO = "#ffffff"
REINTENTO_S = 3
REFRESCO_MS = 1000

POS_ID, POS_LOCATION, POS_VOLUME, POS_STATUS = 0, 1, 2, 3
STATUS_COLORS = {
    "AVAILABLE": "#00ff2f",
    "WATERING": "#00ff2f",
    "LEAK": "#dd1529",
    "OUT_OF_SERVICE": "#ff7300",
    "OFFLINE": "#9ca0a3"
}

sock = None
conectado = False
lock_envio = threading.Lock()
cola = queue.Queue()

########## RED ##########
def recv_exact(s, n):
    data = b""
    while len(data) < n:
        paquete = s.recv(n - len(data))
        if not paquete:
            return None
        data += paquete
    return data


def recv_msg(s):
    header = recv_exact(s, HEADER)
    if header is None:
        return None
    cuerpo = recv_exact(s, int(header.decode(FORMAT).strip()))
    return None if cuerpo is None else cuerpo.decode(FORMAT)


def send(msg):
    global conectado
    if not conectado or sock is None:
        return False
    try:
        message = msg.encode(FORMAT)
        send_length = str(len(message)).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        with lock_envio:
            sock.sendall(send_length)
            sock.sendall(message)
        return True
    except Exception as e:
        print(f"[ERROR] Fallo al enviar: {e}")
        conectado = False
        return False


def conectar():
    global sock, conectado
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4.0)
        s.connect(ADDR_CENTRAL)
        message = f"REGISTRO_FO#{ID_OPERARIO}".encode(FORMAT)
        cab = str(len(message)).encode(FORMAT)
        cab += b' ' * (HEADER - len(cab))
        s.sendall(cab)
        s.sendall(message)
        respuesta = recv_msg(s)
        s.settimeout(None)
        if respuesta is None or not respuesta.startswith("STATUS#OK"):
            s.close()
            return False, f"Central rechazo el registro: {respuesta}"
        sock = s
        conectado = True
        return True, respuesta
    except Exception as e:
        return False, str(e)


def hilo_red():
    global conectado
    while True:
        if not conectado:
            ok, info = conectar()
            if ok:
                cola.put(("estado", "", "black"))
            else:
                cola.put(("estado", "Imposible conectar con WM_Central. Reintentando...", "red"))
                time.sleep(REINTENTO_S)
            continue
        try:
            msg = recv_msg(sock)
            if msg is None:
                raise ConnectionError("Central cerro la conexion")
        except Exception:
            conectado = False
            try:
                sock.close()
            except Exception:
                pass
            cola.put(("log", "[ERROR] Imposible conectar con WM_Central"))
            continue

        if msg.startswith("{"):
            try:
                cola.put(("tabla", json.loads(msg)))
            except json.JSONDecodeError:
                pass
        elif msg.startswith("HOLA CLIENTE"):
            pass
        else:
            cola.put(("log", f"[CENTRAL] {msg}"))


########## GUI ##########
def ws_seleccionada():
    sel = tabla.selection()
    if sel:
        return tabla.item(sel[0], "values")
    return None


def pedir_riego():
    ws = ws_seleccionada()
    if not ws:
        messagebox.showinfo("WM_FO", "Selecciona primero una estacion.")
        return
    if ws[POS_STATUS] != "AVAILABLE":
        messagebox.showwarning("WM_FO", f"La estacion {ws[POS_ID]} no esta disponible ({ws[POS_STATUS]}).")
        return
    if send(f"SOLICITUD_RIEGO#{ws[POS_ID]}#{ID_OPERARIO}"):
        pintar_log(f"[FO] Solicitud de riego enviada a {ws[POS_ID]}")
    else:
        messagebox.showerror("WM_FO", "Imposible conectar con WM_Central.")


def pintar_log(texto):
    txt_log.config(state=tk.NORMAL)
    txt_log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {texto}\n")
    txt_log.see(tk.END)
    txt_log.config(state=tk.DISABLED)


def pintar_tabla(datos):
    ws_sel = ws_seleccionada()
    id_sel = ws_sel[POS_ID] if ws_sel else None
    for fila in tabla.get_children():
        tabla.delete(fila)
    for est in datos.get("estaciones", []):
        fila = tabla.insert("", tk.END, values=est, tags=(est[POS_STATUS],))
        if id_sel is not None and str(est[POS_ID]) == str(id_sel):
            tabla.selection_set(fila)


def procesar_cola():
    try:
        while True:
            item = cola.get_nowait()
            if item[0] == "estado":
                lbl_estado.config(text=item[1], fg=item[2])
            elif item[0] == "tabla":
                pintar_tabla(item[1])
            elif item[0] == "log":
                pintar_log(item[1])
    except queue.Empty:
        pass
    root.after(200, procesar_cola)


def pedir_lista():
    send("LIST_WS")
    root.after(REFRESCO_MS, pedir_lista)


def cerrar():
    send(FIN)
    try:
        sock.close()
    except Exception:
        pass
    root.destroy()


def apartado_grafico():
    global root, tabla, txt_log, lbl_estado
    root = tk.Tk()
    root.title(f"WM_FO - Operario {ID_OPERARIO}")
    root.geometry("800x500")

    barra = tk.Frame(root, bg=COLOR_BLANCO, bd=2, relief=tk.RAISED)
    barra.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
    tk.Button(barra, text="Request watering", bg=STATUS_COLORS["AVAILABLE"],
              command=pedir_riego).pack(side=tk.LEFT, padx=5, pady=5)
    lbl_estado = tk.Label(barra, text="", bg=COLOR_BLANCO, fg="black")
    lbl_estado.pack(side=tk.RIGHT, padx=10)

    marco = tk.Frame(root)
    marco.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
    tabla = ttk.Treeview(marco, columns=("ID", "Location", "Volume", "Status"), show="headings", height=8)
    for col, txt, ancho in (("ID", "ID Station", 100), ("Location", "Location", 250),
                            ("Volume", "Accumulated Volume", 200), ("Status", "Status", 150)):
        tabla.heading(col, text=txt, anchor="w")
        tabla.column(col, width=ancho, anchor="w")
    for estado, color in STATUS_COLORS.items():
        tabla.tag_configure(estado, background=color)
    sb = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=sb.set)
    tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    tk.Label(root, text="MENSAJES DE CENTRAL", bg="#333333", fg="white",
             font=("Arial", 9, "bold")).pack(side=tk.TOP, fill=tk.X, padx=5)
    txt_log = tk.Text(root, height=8, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff2f", font=("Courier", 9))
    txt_log.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5)
    txt_log.config(state=tk.DISABLED)

    root.protocol("WM_DELETE_WINDOW", cerrar)
    procesar_cola()
    pedir_lista()
    root.mainloop()


########## MAIN ##########
# Formato: python WM_FO.py <IP_CENTRAL> <PORT_CENTRAL> <ID_OPERARIO>
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Oops!. Parece que faltan argumentos.")
        print("Uso correcto: python WM_FO.py <IP_CENTRAL> <PORT_CENTRAL> <ID_OPERARIO>")
        sys.exit(1)

    IP_CENTRAL = sys.argv[1]
    PORT_CENTRAL = int(sys.argv[2])
    ID_OPERARIO = sys.argv[3]
    ADDR_CENTRAL = (IP_CENTRAL, PORT_CENTRAL)

    threading.Thread(target=hilo_red, daemon=True).start()
    apartado_grafico()