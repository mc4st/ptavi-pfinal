#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys

# Cliente UDP simple.

# Dirección IP del servidor.
if len(sys.argv) == 3:
    METHOD = sys.argv[1]
    direction = sys.argv[2]
    (receptor, SIPport) = direction.split(":")
    SIPport = int(SIPport)
    (name, SERVER) = receptor.split("@")
else:
    sys.exit("Usage: client.py method receiver@IP:SIPport")

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((SERVER, SIPport))

# Contenido que vamos a enviar
PETICION = METHOD + " " + "sip:" + name + "@" + SERVER + " " + "SIP/2.0"
print("Enviando: " + PETICION)
my_socket.send(bytes(PETICION, 'utf-8') + b'\r\n' + b'\r\n')
data = my_socket.recv(1024)
print('Recibido -- ', data.decode('utf-8'))
datosrecibidos = data.decode('utf-8')
datos = datosrecibidos.split()
if datos[1] == "100" and datos[4] == "180" and datos[7] == "200":
    METHOD = "ACK"
    PETICION = METHOD + " " + "sip:" + name + "@" + SERVER + " " + "SIP/2.0"
    print("Enviando: " + PETICION)
    my_socket.send(bytes(PETICION, 'utf-8') + b'\r\n' + b'\r\n')

print("Terminando socket...")

# Cerramos todo
my_socket.close()
print("Fin.")
