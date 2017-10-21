import threading as th
import get_ip_address as gia
from socket import *

def send():
  s = socket(AF_INET, SOCK_DGRAM)
  s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
  s.sendto('HELLO', ('255.255.255.255', 12345))
  
def receive():
  # LOCAL VARIABLES
  local_ip = gia.get_lan_ip()
  nodes = []
  s = socket(AF_INET, SOCK_DGRAM)
  
  # SOCKET BINDING
  s.bind(('',12345))
  while True:
    m = s.recvfrom(1024)
    
    # GET SOURCE IP ADDRESS
    sender = m[1][0]
    if sender != local_ip and sender not in nodes:
      nodes.append(sender)
      s.sendto('response',(m[1][0], 12345))
    print nodes
  
def start():
  #CREATING THREADS
  sending = th.Thread(target = send, name = send)
  listen = th.Thread(target = receive, name = receive)
  
  #STARTING THREADS
  listen.start()
  sending.start()
  
  
start()