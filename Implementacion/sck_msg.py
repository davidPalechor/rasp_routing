import threading as th
import get_ip_address as gia
import routing
import bd_connect
from socket import *
import json

class Conexion:

  def __init__(self):
    self.neighbors = []
    self.src_address = ""
    self.trg_address = ""
    self.hop_count = 0
    self.broadcast_id = 0
    self.trg_sequence = 0
    self.src_sequence = 0

  def broadcast(self):
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.sendto('HELLO', ('255.255.255.255', 12345))

  def send(self, target, msg, next_hop):
    if self.hop_count == 0:
      self.src_address = gia.get_lan_ip()
      self.src_sequence += 1
      self.broadcast_id += 1
      
    if msg == "rreq":
      message = {
        'type': msg,
        'source_addr': self.src_address,
        'source_sequence': self.src_sequence,
        'broadcast_id': self.broadcast_id,
        'dest_addr':target,
        'dest_sequence':"",
        'hop_cnt':self.hop_count
      }
    elif msg == "rrep":
      message = {
        'type':msg,
        'source_addr':self.src_address,
        'dest_addr': target,
        'dest_sequence':self.trg_sequence,
        'hop_cnt':self.hop_count,
        'lifetime':""
      }

    s = socket(AF_INET, SOCK_DGRAM)
    s.sendto(json.dumps(message), (next_hop, 12345))

  def receive(self):
    s = socket(AF_INET, SOCK_DGRAM)

    # SOCKET BINDING
    s.bind(('', 12345))
    while True:
      m = s.recvfrom(1024)
      packet = m[0]
      print packet
      if '{' in packet:
        packet = eval(packet)
        if packet.get('dest_addr') == self.src_address:
          pass
        else:
          self.src_address = packet.get('source_addr')
          self.src_sequence = packet.get('source_sequence')
          self.hop_count = int(packet.get('hop_cnt')) + 1
          self.broadcast_id = int(packet.get('broadcast_id'))

          next_hop = m[1][0]
          
          routing_list = (
            self.src_address,
            next_hop,
            "",
            self.hop_count,
            1,
            1,
          )

          if bd_connect.consult_duplicate((self.src_address, self.broadcast_id,)):
            pass
            #SE TIENE EL RREQ DEL DESTINO, SE DESECHA EL MENSAJE 
          else:
            # routing.write((',').join(str(x) for x in routing_list))
            bd_connect.insert_routing_table(routing_list)
            bd_connect.insert_rreq((self.src_address, self.broadcast_id))

            for ngh in self.neighbors:
              self.send(packet.get('dest_addr'), 'rreq', ngh)


  # def receive(self):
  #   # LOCAL VARIABLES
  #   #local_ip = gia.get_lan_ip()
  #   #nodes = []
  #   s = socket(AF_INET, SOCK_DGRAM)
    
  #   # SOCKET BINDING
  #   s.bind(('',12345))
  #   while True:
  #     m = s.recvfrom(1024)
      
  #     # GET SOURCE IP ADDRESS
  #     sender = m[1][0]
  #     if sender != local_ip and sender not in nodes:
  #       nodes.append(sender)
  #       s.sendto('response',(sender, 12345))
  #     print nodes

  def find_route(self):
    msg = {}

  def start(self):
    #CREATING THREADS
    sending = th.Thread(target = self.broadcast, name = self.broadcast)
    listen = th.Thread(target = self.receive, name = self.receive)
    
    #STARTING THREADS
    listen.start()
    sending.start()

if __name__ == '__main__':
  con = Conexion()
  con.start()