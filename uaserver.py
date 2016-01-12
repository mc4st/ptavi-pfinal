#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

if len(sys.argv) == 2:
    configXML = sys.argv[1]
else:
    sys.exit('Usage: python3 uaserver.py config')

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
fich_audio = listXML[5][1]['path']

class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            line_bytes = self.rfile.read()
            line = line_bytes.decode('utf-8')
            if not line:
                break
            print("El cliente nos manda: \n" + line_bytes.decode('utf-8'))
            if not line:
                break
            list_recv = line.split()
            METHOD = list_recv[0]
            if METHOD not in ["INVITE", "BYE", "ACK"]:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" + b"\r\n" +
                                 b"\r\n")
            elif METHOD == "INVITE":
                self.wfile.write(b"SIP/2.0 100 Trying" + b"\r\n" + b"\r\n")
                self.wfile.write(b"SIP/2.0 180 Ring" + b"\r\n" + b"\r\n")
                PETICION = "SIP/2.0 200 OK" + "\r\n" + "\r\n"
                PETICION += "Content-Type: application/sdp\r\n\r\n"
                PETICION += "v=0\r\n"
                PETICION += "o=" + user + " " + ua_ip + "\r\n"
                PETICION += "s=misesion\r\n"
                PETICION += "t=0\r\n"
                PETICION += "m=audio8 " + audio_port + " RTP\r\n\r\n"
                self.wfile.write(bytes(PETICION, 'utf-8') + b'\r\n' + b'\r\n')
            elif METHOD == "BYE":
                self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n" + b"\r\n")
            elif METHOD == "ACK":
                print("recibo ACK")
                aEjecutar = './mp32rtp -i ' + IP + ' -p 23032 < ' + fich_audio
                print("Vamos a ejecutar: ", aEjecutar)
                os.system(aEjecutar)
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n" +
                                 b"\r\n")
if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer((ua_ip, int(ua_port)), EchoHandler)
    print("Listening...")
    serv.serve_forever()
