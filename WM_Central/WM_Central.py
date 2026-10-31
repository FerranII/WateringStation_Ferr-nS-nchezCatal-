import socket
import threading
import json
import time
import sqlite3
import os

from kafka import KafkaConsumer, KafkaProducer

HEADER = 64
PORT = 5050
SERVER = "0.0.0.0" 
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 250
POS_ID, POS_LOCATION, POS_VOLUME, POS_STATUS = 0, 1, 2, 3

clientes_monitores = {}
LOCK_MONITORES = threading.Lock()

def send(msg, client):
    try:
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)
    except Exception as e:
        print(f"[ERROR SEND] No se pudo enviar mensaje al cliente: {e}")

############# ESTADOS ###############################    
ESTADOS_VALIDOS = ["AVAILABLE", "WATERING", "LEAK", "OUT_OF_SERVICE", "OFFLINE"]

def estado_AVAILABLE(i):
    global AVAILABLE
    if(i): AVAILABLE += 1
    else: AVAILABLE = max(0, AVAILABLE - 1)

def estado_WATERING(i):
    global WATERING
    if(i): WATERING += 1
    else: WATERING = max(0, WATERING - 1)

def estado_LEAK(i):
    global LEAK
    if(i): LEAK += 1
    else: LEAK = max(0, LEAK - 1)

def estado_OUT_OF_SERVICE(i):
    global OUT_OF_SERVICE
    if(i): OUT_OF_SERVICE += 1
    else: OUT_OF_SERVICE = max(0, OUT_OF_SERVICE - 1)

def estado_OFFLINE(i):
    global OFFLINE
    if(i): OFFLINE += 1
    else: OFFLINE = max(0, OFFLINE - 1)
          
############# BASE DATOS ###############################
if os.path.exists("/data"):
    DB_PATH = "/data/WS_BaseDatos.db"
else:
    DB_PATH = "WS_BaseDatos.db"

def inicializar_db():
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS WS (
                ID TEXT PRIMARY KEY,
                Location TEXT,
                Volume REAL DEFAULT 0.0,
                Status TEXT DEFAULT 'OFFLINE'
            )
        """)
        conexion.commit()
        conexion.close()
        print("[DB] Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"[DB ERROR] No se pudo crear la tabla: {e}")
               
def obetener_WS(ID):
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("SELECT ID, Location, Volume, Status FROM WS WHERE ID = ?", (ID,))
        resultado = cursor.fetchone()
        conexion.close()
        return resultado
    except Exception as e:
        print(f"[DB ERROR] No se pudo leer la base de datos: {e}")
        return []

def obtener_todas_WS():
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("SELECT ID, Location, Volume, Status FROM WS ORDER BY ID ASC")
        resultados = cursor.fetchall()
        conexion.close()
        return resultados
    except Exception as e:
        print(f"[DB ERROR] No se pudo leer la base de datos: {e}")
        return []

def insertar_WS(ID, Location):
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""INSERT OR IGNORE INTO WS (ID, Location) VALUES (?, ?)""", (ID, Location))
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"[DB ERROR]: {e}")

def delete_WS(ID):
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM WS WHERE ID = ?", (ID,))
        conexion.commit()
        conexion.close()
        print(f"[DB SUCCESS] Estación {ID} eliminada correctamente.")
    except Exception as e:
        print(f"[DB ERROR]: {e}")

def actualizar_volumen_WS(ID, volume):
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""UPDATE WS SET Volume = ? WHERE ID = ?""", (float(volume), ID))
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"[DB ERROR] No se pudo actualizar el volumen: {e}")
        
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
        conexion = sqlite3.connect(DB_PATH)
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

############### ATENDER CONEXIONES #######################
def start():
    global NUMERO_CLIENTES
    server.listen()
    print(f"[LISTENING] Servidor backend a la escucha en {SERVER}:{PORT}")
    while True:
        conn, addr = server.accept()
        if (NUMERO_CLIENTES <= MAX_CONEXIONES):
            NUMERO_CLIENTES += 1
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
            print(f"CLIENTES ACTIVOS: {NUMERO_CLIENTES}")
        else:
            print("OOppsss... DEMASIADAS CONEXIONES.")
            send("OOppsss... DEMASIADAS CONEXIONES.", conn)
            conn.close()
            
############# RESPONDER CLIENTES ###############################
def handle_client(conn, addr):
    print(f"[NUEVA CONEXION] {addr} connected.")
    connected = True
    while connected:
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)
                if msg == FIN:
                    connected = False
                    
                elif "REGISTRO_M" in msg:
                    partes = msg.split('#')
                    if(len(partes) == 3):
                        ID_ESTACION = partes[1]
                        LOCATION = partes[2]
                        print(f"Recibida trama registro - ID: {ID_ESTACION} | Location: {LOCATION}")
                        with LOCK_MONITORES: clientes_monitores[ID_ESTACION] = conn
                        send(f"STATUS#OK#Estacion registrada correctamente", conn)
                        insertar_WS(ID_ESTACION, LOCATION)
                        actualizar_estado_WS(ID_ESTACION, "AVAILABLE")
                    else:
                        send(f"STATUS#ERROR#Trama incorrecta", conn)       
                elif "REGISTRO_FO" in msg:
                    partes = msg.split('#')
                    if len(partes) == 2:
                        id_operario = partes[1]
                        print(f"[REGISTRO FO] Operario conectado: {id_operario}")
                        send(f"STATUS#OK#Operario registrado correctamente", conn)
                    else:
                        send("STATUS#ERROR#Trama de registro FO incorrecta", conn)
                        
                elif "STATUS_ENGINE" in msg:
                    partes = msg.split('#')
                    if len(partes) == 6:
                        id_estacion = partes[1]
                        estado_engine = partes[2]
                        accum_volume = partes[4]
                        
                        actualizar_volumen_WS(id_estacion, accum_volume)
                        datos_ws = obetener_WS(id_estacion)
                        estado_actual = datos_ws[POS_STATUS] if datos_ws else "OFFLINE"
                        
                        if estado_engine == "OK":
                            if(estado_actual == "LEAK"):
                                print("Arreglo avería")
                                actualizar_estado_WS(id_estacion, "AVAILABLE")
                        elif estado_engine == "KO":
                            if(estado_actual != "LEAK"): actualizar_estado_WS(id_estacion, "LEAK")
                    else:
                        datos_ws = obetener_WS(id_estacion)
                        estado_actual = datos_ws[POS_STATUS] if datos_ws else "OFFLINE"
                        if(estado_actual != "LEAK"): actualizar_estado_WS(id_estacion, "LEAK")
                elif "SOLENOID" in msg or "ACTIVATE" in msg or "DELETE" in msg:
                    print(f"[COMANDO UI] Recibido desde panel local: {msg}")
                    partes = msg.split('#')
                    if partes[0] == "SOLENOID" and len(partes) == 3:
                        ws_id, accion = partes[1], partes[2]
                        with LOCK_MONITORES: conn_ws = clientes_monitores.get(ws_id)
                        if conn_ws:
                            send(f"SOLENOID#{accion}", conn_ws)
                            if accion == "OPEN":
                                actualizar_estado_WS(ws_id, "WATERING")
                            elif accion == "CLOSE":
                                actualizar_estado_WS(ws_id, "OUT_OF_SERVICE")
                    elif partes[0] == "ACTIVATE" and len(partes) == 2:
                        actualizar_estado_WS(partes[1], "AVAILABLE")
                    elif partes[0] == "DELETE" and len(partes) == 2:
                        delete_WS(partes[1])
                        
                elif "GET_ALL_WS" in msg:
                    estaciones = obtener_todas_WS()
                    resumen = {
                        "AVAILABLE": AVAILABLE,
                        "WATERING": WATERING,
                        "LEAK": LEAK,
                        "OUT_OF_SERVICE": OUT_OF_SERVICE,
                        "OFFLINE": OFFLINE,
                        "estaciones": estaciones
                    }
                    send(json.dumps(resumen), conn)
                           
                else:
                    print(f"He recibido del cliente [{addr}] el mensaje: {msg}")
                    send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ", conn)
        except Exception as e:
            print(f"[ERROR CONEXION] {e}")
            break
            
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()
    
#################### START IRRIGATION #######################
def check_irrigation(ID):
    datos_ws = obetener_WS(ID)
    if(datos_ws and datos_ws[POS_STATUS] == "AVAILABLE"):
        return True
    return False

######################### MAIN ##########################
if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    NUMERO_CLIENTES = 0
    WATERING, AVAILABLE, LEAK, OUT_OF_SERVICE, OFFLINE = 0, 0, 0, 0, 0

    print("Conectado central")
    estaciones = obtener_todas_WS()
    for estacion in estaciones:
        actualizar_estado_WS(estacion[POS_ID], "OFFLINE")
        print(f"Estación ID: {estacion[POS_ID]}, Ubicación: {estacion[POS_LOCATION]}, Volume: {estacion[POS_VOLUME]}, Status: {estacion[POS_STATUS]}")
    OFFLINE = len(estaciones)
    WATERING, AVAILABLE, LEAK, OUT_OF_SERVICE = 0, 0, 0, 0

    inicializar_db()
    
    hilo_servidor = threading.Thread(target=start, daemon=True)
    hilo_servidor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SHUTDOWN] Servidor detenido.")