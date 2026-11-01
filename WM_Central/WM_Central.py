import socket
import threading
import json
import time
import sqlite3
import os
import shutil
from kafka import KafkaConsumer, KafkaProducer

HEADER = 64
PORT = 5050
SERVER = "0.0.0.0" 
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 250
POS_ID, POS_LOCATION, POS_VOLUME, POS_STATUS = 0, 1, 2, 3
ESTADOS_VALIDOS = ["AVAILABLE", "WATERING", "LEAK", "OUT_OF_SERVICE", "OFFLINE"]

clientes_monitores = {}
LOCK_MONITORES = threading.Lock()
LATIDO_TIMEOUT = 5

clientes_operarios = {}
riegos_activos = {}
LOCK_ENVIO = threading.Lock()

historial_kafka = []

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

############# BASE DE DATOS ###############################
if os.path.exists("/data"):
    DB_PATH = "/data/WS_BaseDatos.db"
    if not os.path.exists(DB_PATH) and os.path.exists("WS_BaseDatos.db"): shutil.copy("WS_BaseDatos.db", DB_PATH)
else:
    DB_PATH = "WS_BaseDatos.db"

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
        send_kafka("ELIMINACION_ESTACION", ID, "OFFLINE")
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
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()

        cursor.execute("SELECT Status FROM WS WHERE ID = ?", (ID,))
        resultado = cursor.fetchone()
        if not resultado:          # la estación no existe (p. ej. borrada)
            conexion.close()
            return
        old_estado = resultado[0]

        cursor.execute("UPDATE WS SET Status = ? WHERE ID = ?", (Status, ID))
        conexion.commit()
        conexion.close()

        print(f"[DB SUCCESS] Estación {ID} actualizada de '{old_estado}' a '{Status}'.")
        send_kafka("CAMBIO_ESTADO", ID, Status)
    except Exception as e:
        print(f"[DB ERROR] No se pudo resolver el estado: {e}")
        
############# KAFKA ############################################################
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")

try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Productor conectado")
except Exception as e:
    print(f"No se pudo conectar a Kafka: {e}")
    producer = None
    
def send_kafka(tipo_evento, id_estacion, estado, ubicacion=""):
    texto_log = f"[{time.strftime('%H:%M:%S')}] {tipo_evento} -> Estación {id_estacion} ({estado})"
    with LOCK_MONITORES:
        historial_kafka.append(texto_log)
        if len(historial_kafka) > 50: historial_kafka.pop(0)
        
    if not producer: return
    try:
        mensaje = {
            "evento": tipo_evento,
            "id_estacion": id_estacion,
            "estado": estado,
            "ubicacion": ubicacion,
            "timestamp": time.time()
        }
        producer.send("Watering_Station", value=mensaje)
        producer.flush()
        print(f"[KAFKA] Evento enviado: {tipo_evento} -> Estación {id_estacion}")
    except Exception as e:
        print(f"[KAFKA ERROR] Fallo al enviar mensaje a Kafka: {e}")
############### ATENDER CONEXIONES #######################
def start():
    global NUMERO_CLIENTES
    server.listen()
    print(f"[LISTENING] Servidor backend a la escucha en {SERVER}:{PORT}")
    while True:
        conn, addr = server.accept()
        if (NUMERO_CLIENTES < MAX_CONEXIONES):
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
    global NUMERO_CLIENTES
    connected = True
    id_registro = None
    print(f"[NUEVA CONEXION] {addr} connected.")
    try:
        while connected:
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
                        conn.settimeout(LATIDO_TIMEOUT)
                        conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                        
                        id_registro = ID_ESTACION
                        insertar_WS(ID_ESTACION, LOCATION)
                        actualizar_estado_WS(ID_ESTACION, "AVAILABLE")
                        send_kafka("REGISTRO_ESTACION", ID_ESTACION, "AVAILABLE", LOCATION)
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
                                send_kafka("ARREGLADO_LEAK", id_estacion, "AVAILABLE")
                        elif estado_engine == "KO":
                            if(estado_actual != "LEAK"): 
                                actualizar_estado_WS(id_estacion, "LEAK")
                                send_kafka("ALERTA_LEAK", id_estacion, "LEAK")
                    elif len(partes) >= 2:
                        id_estacion = partes[1]
                        datos_ws = obetener_WS(id_estacion)
                        estado_actual = datos_ws[POS_STATUS] if datos_ws else "OFFLINE"
                        if estado_actual != "LEAK":
                            actualizar_estado_WS(id_estacion, "LEAK")
                            send_kafka("ALERTA_LEAK", id_estacion, "LEAK")
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
                    with LOCK_MONITORES:
                        logs_actuales = list(historial_kafka)
                        historial_kafka.clear()

                    conteo = {e: 0 for e in ESTADOS_VALIDOS}
                    for est in estaciones:
                        if est[POS_STATUS] in conteo:
                            conteo[est[POS_STATUS]] += 1

                    resumen = {**conteo, "estaciones": estaciones, "logs_kafka": logs_actuales}
                    send(json.dumps(resumen), conn)
                           
                else:
                    print(f"He recibido del cliente [{addr}] el mensaje: {msg}")
                    send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ", conn)
                    
            else:
                break
    except socket.timeout:
        print(f"[LATIDO PERDIDO] {addr} ({id_registro}) lleva más de {LATIDO_TIMEOUT}s sin enviar mensajes")
    except Exception as e:
        print(f"[ERROR CONEXION] {e}")
        
    finally:
        with LOCK_MONITORES:
            NUMERO_CLIENTES -= 1
            es_la_actual = bool(id_registro) and clientes_monitores.get(id_registro) is conn
            if es_la_actual:
                del clientes_monitores[id_registro]

        if es_la_actual:
            print(f"La estación {id_registro} se ha desconectado")
            actualizar_estado_WS(id_registro, "OFFLINE")
            send_kafka("DESCONEXION_MONITOR", id_registro, "OFFLINE")
            
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
    
    hilo_servidor = threading.Thread(target=start, daemon=True)
    hilo_servidor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SHUTDOWN] Servidor detenido.")