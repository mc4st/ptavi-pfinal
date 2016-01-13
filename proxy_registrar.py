#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import socketserver
import socket
import sys
import json
import time
import random
import hashlib

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

if len(sys.argv) == 2:
    configXML = sys.argv[1]
else:
    sys.exit('Usage: python3 proxy_registrar.py config')


class ExtraerXML (ContentHandler):
    def __init__(self):
        self.taglist = []
        self.tags = [
            'server', 'database', 'log']
        self.diccattributes = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']}

    def startElement(self, tag, attrs):
        # si existe la etiqueta en mi lista de etiquetas.
        if tag in self.tags:
            # recorro todos los atributos, guardo en diccionario.
            dicc = {}
            for attribute in self.diccattributes[tag]:
                if attribute == 'ip':
                    dicc[attribute] = attrs.get(attribute, "")
                    ip_server = dicc[attribute]
                    if ip_server == "":
                        ip_server = "127.0.0.1"
                else:
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
user = listXML[0][1]['name']
ip_server = listXML[0][1]['ip']
port_server = int(listXML[0][1]['puerto'])


def log(formato, hora, evento):
    fich = listXML[2][1]['path']
    fich_log = open(fich, 'a')
    formato = '%Y%m%d%H%M%S'
    hora = time.gmtime(hora)
    formato_hora = fich_log.write(time.strftime(formato, hora))
    evento = evento.replace('\r\n', ' ')
    fich_log.write(evento + '\r\n')
    fich_log.close()


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    DiccServer = {}
    DiccNonce = {}

    def register2json(self):
        with open("register.json", 'w') as fichero_json:
            json.dump(self.DiccServer, fichero_json)

    def json2register(self):
        try:
            with open("register.json", 'r') as existe:
                self.DiccServer = json.load(existe)
        except:
            pass

    def deleteDiccServer(self):
        new_list = []
        formato = '%Y-%m-%d %H:%M:%S'
        for clave in self.DiccServer:
            time_now = self.DiccServer[clave][3]
            print(time_now)
            if time.strptime(time_now, formato) <= time.gmtime(time.time()):
                new_list.append(clave)
        for usuario in new_list:
            del self.DiccServer[usuario]

    def SearchPasswd(self, dir_user):
        fich_passwd = open("passwd.txt")
        datos_user = fich_passwd.read()
        passwd = ''
        for line in datos_user.split('\n'):
            if line != '':
                user_fich = line.split(" ")[0]
                passwd_fich = line.split(" ")[1]
                if user_fich == dir_user:
                    passwd = passwd_fich
        return passwd

    def handle(self):
        IP = self.client_address[0]
        PORT = self.client_address[1]
        #if len(self.DiccServer) == 0:
        #    self.json2register()
        #    self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n" + b"\r\n")
        while 1:
            line_bytes = self.rfile.read()
            print("El cliente nos manda: \n" + line_bytes.decode('utf-8'))
            line = line_bytes.decode('utf-8')
            if not line:
                break
            list_recv = line.split()
            METHOD = list_recv[0]
            if METHOD not in ["REGISTER", "INVITE", "BYE", "ACK"]:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" + b"\r\n" +
                                 b"\r\n")
                hora = time.time()
                evento = " Sent to " + IP + ':' + str(PORT) + ':'
                evento += "SIP/2.0 405 Method Not Allowed" + '\r\n'
                log('', hora, evento)
            if METHOD == "REGISTER":
                address_port = list_recv[1]
                address_divided = address_port.split(':')
                address = address_divided[1]
                port = address_divided[2]
                expires = list_recv[4]
                nonce = random.randint(100000000000000000000,
                                       999999999999999999999)
                if len(list_recv) == 5:
                    time_now = int(time.time()) + int(expires)
                    formato = '%Y-%m-%d %H:%M:%S'
                    hora = time.gmtime(time_now)
                    time_expires = time.strftime(formato, hora)
                    self.DiccServer[address] = [str(IP), port, expires,
                                                str(time_expires)]
                    PETICION = "SIP/2.0 401 Unauthorized" + "\r\n"
                    PETICION += "WWW Authenticate: nonce=" + str(nonce)
                    self.wfile.write(bytes(PETICION, 'utf-8') + b"\r\n")
                    self.DiccNonce[address] = nonce
                    hora = time.time()
                    evento = " Sent to " + IP + ':' + str(PORT) + ':'
                    evento += PETICION + '\r\n'
                    log('', hora, evento)
                    if int(expires) == 0:
                        del self.DiccServer[address]
                if len(list_recv) == 8:
                    #comparar response que llega del client con el response
                    #creado por pr
                    response_recv = list_recv[7]
                    passwd_fich = self.SearchPasswd(address)
                    nonce_env = str(self.DiccNonce[address])
                    nonce_bytes = bytes(nonce_env, 'utf-8')
                    passwd = bytes(passwd_fich, 'utf-8')
                    m = hashlib.md5()
                    m.update(passwd + nonce_bytes)
                    response_new = m.hexdigest()
                    if response_recv == response_new:
                        self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n")
                        hora = time.time()
                        evento = " Sent to " + IP + ':' + str(PORT) + ':'
                        evento += "SIP/2.0 200 OK" + '\r\n'
                        log('', hora, evento)
                        self.deleteDiccServer()
                        self.register2json()
            elif METHOD == "INVITE":
                address_sip = list_recv[1]
                address_divided = address_sip.split(':')
                address = address_divided[1]
                if address in self.DiccServer:
                    ua_ip = self.DiccServer[address][0]
                    ua_port = int(self.DiccServer[address][1])

                    my_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_REUSEADDR, 1)
                    my_socket.connect((ua_ip, int(ua_port)))

                    my_socket.send(bytes(line, 'utf-8') + b'\r\n' + b'\r\n')
                    data = my_socket.recv(ua_port)
                    print('Recibido -- ', data.decode('utf-8'))
                    datosrecibidos = data.decode('utf-8')
                    datos = datosrecibidos.split()
                    self.wfile.write(bytes(datosrecibidos, 'utf-8') + b'\r\n')
                    hora = time.time()
                    evento = " Received from " + ua_ip + ':' + str(ua_port)
                    evento += ':' + datosrecibidos + '\r\n'
                    log('', hora, evento)
                    hora = time.time()
                    evento = " Sent to " + IP + ':' + str(PORT) + ':'
                    evento += datosrecibidos + '\r\n'
                    log('', hora, evento)
                else:
                    self.wfile.write(bytes("SIP/2.0 404 User not found", 'utf-8'))
                    hora = time.time()
                    evento = " Sent to " + IP + ':' + str(PORT) + ':'
                    evento += "SIP/2.0 404 User not found" + '\r\n'
                    log('', hora, evento)
            elif METHOD == "ACK":
                address_sip = list_recv[1]
                address_divided = address_sip.split(':')
                address = address_divided[1]
                ua_ip = self.DiccServer[address][0]
                ua_port = int(self.DiccServer[address][1])

                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_socket.connect((ua_ip, int(ua_port)))
                my_socket.send(bytes(line, 'utf-8') + b'\r\n' + b'\r\n')
                data = my_socket.recv(PORT)
                datosrecibidos = data.decode('utf-8')

                hora = time.time()
                evento = " Received from " + IP + ':' + str(PORT)
                evento += ':' + datosrecibidos + '\r\n'
                log('', hora, evento)
                hora = time.time()
                evento = " Sent to " + ua_ip + ':' + str(ua_port) + ':'
                evento += datosrecibidos + '\r\n'
                log('', hora, evento)
            elif METHOD == "BYE":
                address_sip = list_recv[1]
                address_divided = address_sip.split(':')
                address = address_divided[1]
                if address in self.DiccServer:
                    ua_ip = self.DiccServer[address][0]
                    ua_port = int(self.DiccServer[address][1])

                    my_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_REUSEADDR, 1)
                    my_socket.connect((ua_ip, int(ua_port)))

                    my_socket.send(bytes(line, 'utf-8') + b'\r\n' + b'\r\n')
                    data = my_socket.recv(ua_port)
                    print('Recibido -- ', data.decode('utf-8'))
                    datosrecibidos = data.decode('utf-8')
                    datos = datosrecibidos.split()
                    self.wfile.write(bytes(datosrecibidos, 'utf-8')
                                     + b'\r\n' + b'\r\n')
                    hora = time.time()
                    evento = " Received from " + IP + ':' + str(PORT)
                    evento += ':' + datosrecibidos + '\r\n'
                    log('', hora, evento)
                    hora = time.time()
                    evento = " Sent to " + ua_ip + ':' + str(ua_port) + ':'
                    evento += datosrecibidos + '\r\n'
                    log('', hora, evento)
if __name__ == "__main__":
    serv = socketserver.UDPServer((ip_server, int(port_server)),
                                  SIPRegisterHandler)
    print("Server MiServidorBingBang listening at port 5555...")
    serv.allow_reuse_address = True
    serv.serve_forever()
    serv.close()
