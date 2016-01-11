#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import os
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Dirección IP del servidor.
if len(sys.argv) == 4:
    configXML = sys.argv[1]
    METHOD = sys.argv[2]
    option = sys.argv[3]
else:
    sys.exit("Usage: client.py config method opcion")

# Creamos extraer fichero xml
class ExtraerXML (ContentHandler):
    def __init__(self):
        self.taglist = []
        self.tags = [
            'account', 'uaserver', 'rtpaudio', 'regproxy', 'log', 'audio']
        self.diccattributes = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']}
            
    def startElement(self, tag, attrs):
        dicc = {}
        # si existe la etiqueta en mi lista de etiquetas.
        if tag in self.tags:
            # recorro todos los atributos, guardo en diccionario.
            for attribute in self.diccattributes[tag]:
                dicc[attribute] = attrs.get(attribute, "")
            # voy encadenando la lista, guardo a continuación sin sustituir
            # lo que tiene dentro.
            self.taglist.append([tag, dicc])

    def get_tags(self):
        return self.taglist

parser = make_parser()
XMLHandler = ExtraerXML()
parser.setContentHandler(XMLHandler)
parser.parse(open(configXML))
listXML = XMLHandler.get_tags()
user = listXML[0][1]['username']
ua_port = listXML[1][1]['puerto']
ua_ip = listXML[1][1]['ip']
audio_port = listXML[2][1]['puerto']
proxy_ip = listXML[3][1]['ip']
proxy_port = int(listXML[3][1]['puerto'])

if ua_ip == "":
    ua_ip = '127.0.0.1'

# Según el tpo de método que recibamos (REGISTER, INVITE, BYE)
if METHOD == 'REGISTER':
    # [1] porque es el diccionario y no la etiqueta
    #REGISTER sip:leonard@bigbang.org:1234 SIP/2.0
    #Expires: 3600
    PETICION = METHOD + " sip:" + user + ":" + ua_port + ": SIP/2.0\r\n"
    PETICION += "Expires: " + option + "\r\n\r\n"

elif METHOD == 'INVITE':
    # INVITE sip:penny@girlnextdoor.com SIP/2.0
    #Content-Type: application/sdp
    #v=0
    #o=leonard@bigbang.org 127.0.0.1
    #s=misesion
    #t=0
    #m=audio 34543 RTP
    PETICION = METHOD + " sip:" + option + " SIP/2.0\r\n"
    PETICION += "Content-Type: application/sdp\r\n\r\n"
    PETICION += "v=0\r\n"
    PETICION += "o=" + user + " " + ua_ip + "\r\n"
    PETICION += "s=misesion\r\n"
    PETICION += "t=0\r\n"
    PETICION += "m=audio8 " + audio_port + " RTP\r\n\r\n"

elif METHOD == 'BYE':
    PETICION = METHOD + " sip:" + option + " SIP/2.0\r\n\r\n"

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((proxy_ip, proxy_port))

# Contenido que vamos a enviar (similar práctica anterior)
print("Enviando: " + PETICION)
my_socket.send(bytes(PETICION, 'utf-8') + b'\r\n' + b'\r\n')
data = my_socket.recv(1024)

print('Recibido -- ', data.decode('utf-8'))
datosrecibidos = data.decode('utf-8')
datos = datosrecibidos.split()
if datos[1] == "100" and datos[4] == "180" and datos[7] == "200":
    METHOD = "ACK"
    PETICION = METHOD + " sip:" + option + " " + "SIP/2.0"
    print("Enviando: " + PETICION)
    my_socket.send(bytes(PETICION, 'utf-8') + b'\r\n' + b'\r\n')

print("Terminando socket...")

# Cerramos todo
my_socket.close()
print("Fin.")
