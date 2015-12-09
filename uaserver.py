#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        IP = self.client_address[0]
        PORT = self.client_address[1]
        fich_audio = sys.argv[3]
        while 1:
            line_bytes = self.rfile.read()
            line = line_bytes.decode('utf-8')
            if not line:
                break
            print("El cliente nos manda: \n" + line_bytes.decode('utf-8'))
            (metodo, address, sip) = line.split()
            if metodo not in ["INVITE", "BYE", "ACK"]:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" + b"\r\n" +
                                 b"\r\n")
            elif metodo == "INVITE":
                self.wfile.write(b"SIP/2.0 100 Trying" + b"\r\n" + b"\r\n")
                self.wfile.write(b"SIP/2.0 180 Ring" + b"\r\n" + b"\r\n")
                self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n" + b"\r\n")
            elif metodo == "BYE":
                self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n" + b"\r\n")
            elif metodo == "ACK":
                aEjecutar = './mp32rtp -i ' + IP + ' -p 23032 < ' + fich_audio
                print("Vamos a ejecutar: ", aEjecutar)
                os.system(aEjecutar)
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n" +
                                 b"\r\n")
if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    PORT = int(sys.argv[2])
    IP = sys.argv[1]
    serv = socketserver.UDPServer((IP, PORT), EchoHandler)
    print("Lanzando servidor UDP de eco...")
    serv.serve_forever()
