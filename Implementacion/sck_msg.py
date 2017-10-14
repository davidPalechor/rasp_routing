from socket import *
import threading as th

def send():
  s = socket(AF_INET, SOCK_DGRAM)
  s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
  s.sendto('Hola mundo', ('255.255.255.255', 12345))
  
def receive():
  s = socket(AF_INET, SOCK_DGRAM)
  s.bind(('',12345))
  while True:
    m = s.recvfrom(1024)
    if m[1][0] != '192.168.0.200':
      s.sendto('respuesta',(m[1][0], 12345))
    print m
  
def start():
  #CREATING THREADS
  sending = th.Thread(target = send, name = send)
  listen = th.Thread(target = receive, name = receive)
  
  #STARTING THREADS
  listen.start()
  sending.start()
  
  
start()