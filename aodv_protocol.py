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
        self.rrep_listen_sock = 0

    
    def notify_network(self, msg):
        if self.neighbors:
            #CONSULT NEIGHBOR IP ADDRESS IN BD ROUTING TABLE
            for ngh in self.neighbors:
                target = bd_connect.consult_target(ngh)
                self.logger.debug("Record %s" % target)
                if target:
                    self.logger.info("Target %s found " % ngh)
                    self.aodv_send(target[0].get('next_hop'),msg)
                else:
                    self.logger.info("Target %s not found" % ngh)
                    self.send_rreq(ngh, -1)

    def receive_neighbors(self):

        while True:
            (new_ngh, _) = self.neighbor_sock.recvfrom(1024) 
            self.neighbors = eval(new_ngh)
            self.logger.debug("Neighbors updated: %s" % self.neighbors)

    def aodv_send(self, destination, message):
        try:
                message_bytes = json.dumps(message)
                self.aodv_sock.sendto(message_bytes, (destination, 1225))
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

    def forward_rreq(self, rreq_message):
        self.logger.debug("Forwarding...")
        rreq_dict = rreq_message

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

    def process_rreq(self,message):
        self.logger.debug("Processing RREQ message %s" %message)
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
        rt_record = bd_connect.consult_target(source_addr)

        if bd_connect.consult_duplicate((source_addr, broadcast_id)):
            self.logger.debug("RREQ duplicate found!")
            return
        elif rt_record:

            # 1. If originator sequence number in packet is bigger than destination sequence in routing table
            #    Update target sequence number in DB.
            #
            # 2. If originator sequence number and destination sequence number are equal, but hop count in DB
            #    is bigger than hop count in packet, update hop count in DB.
            #
            # 3. If detination sequence number is unknown (-1), update sequence number in DB.

            if int(rt_record[0].get("target_seq_number")) < source_sequence:
                bd_connect.update_routing_table("target_seq_number", source_sequence, rt_record[0].get("ID"))
            
            elif int(rt_record[0].get("target_seq_number")) == source_sequence:
                if rt_record[0].get("hop_count") > hop_count:
                    bd_connect.update_routing_table("hop_count", hop_count, rt_record[0].get("ID"))
                    bd_connect.update_routing_table("next_hop", sender, rt_record[0].get("ID"))

            elif int(rt_record[0].get("target_seq_number") == -1):
                bd_connect.update_routing_table("target_seq_number", source_sequence, rt_record[0].get("ID"))

        else:
            #If there's no route to destination, add entry

            bd_connect.insert_routing_table(routing_list)
            bd_connect.insert_rreq((source_addr, broadcast_id))

        # Check if we are the destination. If we are, generate and send an
        # RREP back.
        if (self.localhost == dest_addr): 
                self.send_rrep(source_addr, sender, dest_addr, dest_addr, 0, 0) #todavia no existe

        # We are not the destination. Check if we have a valid route
        # to the destination. If we have, generate and send back an
        # RREP.
        else:
            target = bd_connect.consult_target(dest_addr)
            if (target):
                # Verify that the route is valid and has a higher seq number
                #si ruta Activa -> status = 1 y dest_sequence > dest_sequence_rreq enviar rrep
                if target[0].get("target_seq_number") >=dest_sequence:
                        self.send_rrep(source_addr, sender, self.localhost, dest_addr, target[0].get("target_seq_number"))#todavia no existe
            else:
                self.forward_rreq(message)

    def send_rrep(self, target, next_hop, source_addr, int_node, dest_seq, hop_count):
        self.logger.debug("Send RREP")

        # Check if this node is the destination
        # Update sequence numbers and restart hop count
        if source_addr == int_node:
            self.src_sequence += 1
            dest_seq = self.src_sequence
            hop_count = 0

        # Construct the RREP message
        message = {
            "type" : "msg_rrep",
            "sender" : self.localhost,
            "source_addr" : source_addr,
            "hop_cnt" : hop_count,
            "dest_addr" : target,
            "dest_sequence" : dest_seq
        }

        self.aodv_send(next_hop, message)

    def forward_rrep(self, message, next_hop):
        # There is no need to rebuild the whole RREP, only change
        # the sender IP Address
        self.logger.debug("Forwarding RREP...")
        message["sender"] = self.localhost
        self.aodv_send(next_hop, message)

    def process_rrep(self, message):
        self.logger.debug("Processing RREP message %s" %message)

        sender = message["sender"]
        source_addr = message["source_addr"]
        hop_count = int(message["hop_cnt"]) + 1
        dest_addr = message["dest_addr"]
        dest_sequence = message["dest_sequence"]

        routing_list = (
            source_addr,
            sender,
            dest_sequence,
            hop_count,
            1,
            1,
        )

        if self.localhost == dest_addr:
            if bd_connect.consult_target(source_addr):
                pass
            else:
                bd_connect.insert_routing_table(routing_list)
        else:
            record = bd_connect.consult_target(source_addr)
            if record:
                bd_connect.update_routing_table('status', 1, record[0].get('ID'))
                bd_connect.update_routing_table('target_seq_number', dest_sequence, record[0].get('ID'))
            else:
                bd_connect.insert_routing_table(routing_list)
            
            self.forward_rrep(message, record[0].get('next_hop'))

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

    def unicast_listener(self):
        self.logger.debug("RREP listener ON!")
        while True:
            packet, (sender, _) = self.rrep_listen_sock.recvfrom(1024)
            self.logger.debug("Unicast Packet received from %s" % sender)

            if '{' in packet:
                packet = json.loads(packet)
                if packet.get('type') == 'msg_rrep':
                    self.process_rrep(packet)
            else:                    
                self.logger.info("Unicasted Message received: %s from %s" % (packet, sender))

    def start(self):
        #CREATING SOCKETS
        self.neighbor_sock = socket(AF_INET, SOCK_DGRAM)
        self.neighbor_sock.bind((self.localhost, 1212))

        self.aodv_sock = socket(AF_INET, SOCK_DGRAM)

        self.aodv_brd_sock = socket(AF_INET, SOCK_DGRAM)
        self.aodv_brd_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        self.rcv_sock = socket(AF_INET, SOCK_DGRAM)
        self.rcv_sock.bind(("", 12345))

        self.rrep_listen_sock = socket(AF_INET, SOCK_DGRAM)
        self.rrep_listen_sock.bind((self.localhost, 1225))

        #CREATING THREADS
        neighbors = th.Thread(target = self.receive_neighbors, name = self.receive_neighbors)
        main_listen = th.Thread(target = self.receive, name = self.receive)
        rrep_listener = th.Thread(target = self.unicast_listener, name = self.unicast_listener)
        
        #STARTING THREADS
        neighbors.start()
        main_listen.start()
        rrep_listener.start()