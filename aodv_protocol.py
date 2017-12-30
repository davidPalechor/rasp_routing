#!/usr/bin/python
import threading as th
import get_ip_address as gia
import routing
import bd_connect
from socket import *
import json
import logging

AODV_HELLO_INTERVAL = 10 

class AODV_Protocol:
  
    def __init__(self):
        self.neighbors = []
        self.localhost = gia.get_lan_ip()
        self.src_address = gia.get_lan_ip()
        self.trg_address = ""
        self.hop_count = 0
        self.broadcast_id = 0
        self.trg_sequence = 0
        self.src_sequence = 0
        self.hello_timer = 0
        self.logger = logging.getLogger(__name__)

        self.neighbor_sock = 0
        self.aodv_sock = 0
        self.aodv_brd_sock = 0
        self.rcv_sock = 0

    def receive_neighbors(self):

        while True:
            (new_ngh, _) = self.neighbor_sock.recvfrom(1024) 
            self.neighbors = eval(new_ngh)
            self.logger.debug("Neighbors updated: %s" % self.neighbors)

    def aodv_send(self, destination, message):
        try:
                message_bytes = bytes(message)
                self.aodv_sock.sendto(message_bytes, (destination, 12345))
        except Exception as e:
                self.logger.exception("[aodv_send] Message not sent due to") 

    def aodv_send_broadcast(self, message):
        try:
                self.aodv_brd_sock.sendto(json.dumps(message), ('255.255.255.255', 12345))
                self.logger.debug("Message %s broadcasted" % message)
        except Exception as e:
                self.logger.exception("[aodv_send_broadcast] Message not sent due to")

    def send_rreq(self, target, dest_sequence):
        self.logger.info("Finding route to %s" % target)
        self.src_sequence = self.src_sequence + 1
        self.broadcast_id = self.broadcast_id + 1

        message = {
                'type': "msg_rreq",
                'sender' : self.src_address,        #necesario para saber quien envia el mensaje y diferenciar del origen en reenvio
                'source_addr': self.src_address,
                'source_sequence': self.src_sequence,
                'broadcast_id': self.broadcast_id,
                'dest_addr':target,
                'dest_sequence': dest_sequence,
                'hop_cnt':self.hop_count
        }
        #envio del mensaje en broadcast
        self.aodv_send_broadcast(message)

    def forward_rreq(self,rreq_message):

        rreq_dict = eval(rreq_message)

        message = {
                'type' : rreq_dict['type'],
                'sender' : self.localhost,    
                'source_addr' : rreq_dict['source_addr'],
                'source_sequence' : reeq_dict['source_sequence'],
                'broadcast_id' : rreq.dict['broadcast_id'],
                'dest_addr': rreq_dict['dest_addr'],
                'dest_sequence' : rreq_dict['dest_sequence'],
                'hop_cnt' : rreq_dict['hop_cnt']
        }

        #envio del mensaje en broadcast
        self.aodv_send_broadcast(message)

    
    def send_rrep(self):
        self.logger.debug("Send RREP")

    def send(self, msg):
        if self.neighbors:
            #CONSULT NEIGHBOR IP ADDRESS IN BD ROUTING TABLE
            for ngh in self.neighbors:
                target = bd_connect.consult_target(ngh)
                self.logger.debug("Record %s" % target)
                if target:
                    self.logger.info("Target %s found " % ngh)
                    self.aodv_send(target.get('next_hop'),msg)
                else:
                    self.logger.info("Target %s not found" % ngh)
                    self.send_rreq(ngh, 0)
                    
    def send_hello_message(self):
        try:
            for n in neighbors:
                    message_type = "HELLO_MESSAGE"
                    sender = self.node_id
                    message = message_type + ":" + sender
                    self.aodv_send(n, message)

            # Restart the timer
            self.hello_timer.cancel()
            self.hello_timer = Timer(AODV_HELLO_INTERVAL, self.send_hello_message, ())
            self.hello_timer.start()
        except:
            pass

    def process_rreq(self,message):
        self.logger.debug("Processing %s message" %message)
        message = message
        message_type = message['type']
        sender = message['sender']
        hop_count = int(message['hop_cnt']) + 1
        message['hop_cnt'] = str(hop_count)
        broadcast_id = int(message['broadcast_id'])
        dest_addr = message['dest_addr']
        dest_sequence = int(message['dest_sequence'])
        source_addr = message['source_addr']
        source_sequence = int(message['source_sequence'])

        routing_list =(
                source_addr,
                sender,
                dest_sequence,
                hop_count,
                1,                            #Lifetime
                1,                             #status
        )

        # Discard this RREQ if we have already received this before
        if bd_connect.consult_duplicate((source_addr, broadcast_id)):
            self.logger.debug("RREQ duplicate found!")
            pass
            #SE TIENE EL RREQ DEL DESTINO, SE DESECHA EL MENSAJE 
        elif (bd_connect.consult_target(source_addr)):
            #If we don't have a route for the originator, add an entry
            # comparar si debo actualizar entrada que ya exista de ese origen teniendo en cuenta el protocolo.
            
                #actualizar numeros de secuencia
            pass
        else:
            bd_connect.insert_routing_table(routing_list)
            bd_connect.insert_rreq((source_addr, broadcast_id))

        # Check if we are the destination. If we are, generate and send an
        # RREP back.
        if (self.localhost == dest_addr): 
                self.send_rrep() #todavia no existe

        # We are not the destination. Check if we have a valid route
        # to the destination. If we have, generate and send back an
        # RREP.
        else:
            target = bd_connect.consult_target(dest_addr)
            if (target):
                # Verify that the route is valid and has a higher seq number
                #si ruta Activa -> status = 1 y dest_sequence > dest_sequence_rreq enviar rrep
                if ( target.get('status') == 1 and target.get("target_seq_number") >=dest_sequence    ):
                        self.send_rrep()#todavia no existe
            else:
                self.forward_rreq(message)

    def receive(self):
        self.logger.debug("Receiving Thread ON!")
        while True:
            packet, (sender, _) = self.rcv_sock.recvfrom(1024)
            self.logger.debug("Packet received from %s" % sender)

            if '{' in packet:
                packet = json.loads(packet)
                if packet.get('type') == 'msg_rreq' and packet.get('sender') != self.localhost:
                    self.process_rreq(packet)
            else:
                self.logger.info("Message received: %s from %s" % (packet, sender))

    def find_route(self):
        msg = {}

    def start(self):
        #CREATING SOCKETS
        self.neighbor_sock = socket(AF_INET, SOCK_DGRAM)
        self.neighbor_sock.bind((self.localhost, 1212))

        self.aodv_sock = socket(AF_INET, SOCK_DGRAM)

        self.aodv_brd_sock = socket(AF_INET, SOCK_DGRAM)
        self.aodv_brd_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        self.rcv_sock = socket(AF_INET, SOCK_DGRAM)
        self.rcv_sock.bind(("", 12345))
        #CREATING THREADS
        neighbors = th.Thread(target = self.receive_neighbors, name = self.receive_neighbors)
        #sending = th.Thread(target = self.broadcast, name = self.broadcast)
        listen = th.Thread(target = self.receive, name = self.receive)
        
        #STARTING THREADS
        neighbors.start()
        listen.start()
        #sending.start()