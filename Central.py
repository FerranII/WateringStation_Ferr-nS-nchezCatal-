import tkinter as tk
from tkinter import ttk

STATUS = {
    "AVAILABLE": "#00ff2fcf",
    "WATERING": "#00ff2fcf",
    "LEAK": "#dd1529",
    "OUT_OF_SERVICE": "#ff7300",
    "DISCONNECTED": "#9ca0a3"
}
current_status = {} #Usa ID como llave y STATUS como valor

def cambiar_estado(id, status):    
    if status in STATUS:
        current_status[id] = status
    else:
        current_status[id] = "DISCONNECTED"

    current_color = STATUS[current_status[id]]
    return current_status[id], current_color
