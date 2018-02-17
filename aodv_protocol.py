#!/usr/bin/python
import time
import threading as th
import get_ip_address as gia
import routing
import bd_connect
from socket import *
import json
import logging

AODV_HELLO_INTERVAL = 10
AODV_HELLO_TIMEOUT = 30 

class AODV_Protocol:
  
    def __init__(self):
        self.nodes = []
        self.neighbors = {}
        self.message_pend_list = []
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
        self.return_node_sock = 0
        self.aodv_sock = 0
        self.aodv_brd_sock = 0
        self.rcv_sock = 0
        self.rrep_listen_sock = 0

        self.hello_timer = 0

        self.times_dict = {}
    
    def notify_network(self, msg):
        self.logger.debug("Notifying to nodes %s" % self.nodes)
        if self.nodes: 
            #CONSULT NEIGHBOR IP ADDRESS IN BD ROUTING TABLE
            for ngh in self.nodes:     
                message = {
                    'type': 'notify',
                    'source_addr': self.localhost,
                    'dest_addr': ngh,
                    'data':msg
                }
                target = bd_connect.consult_target(ngh)
                self.logger.debug("Record %s" % target)
                if target:
                    self.logger.info("Target %s found " % ngh)
                    self.send(target[0].get('next_hop'), message)
                else:
                    self.logger.info("Target %s not found" % ngh)

                    self.times_dict[ngh] = time.time()
                    self.send_rreq(ngh, -1)
                    self.message_pend_list.append(message)

    def receive_nodes(self):
        while True:
            (new_nodes, _) = self.neighbor_sock.recvfrom(1024)
            network = eval(new_nodes)
            if self.nodes:
                self.logger.debug("Network nodes %s" % self.nodes)
                if self.nodes != network:
                    notification = {
                        'nodes':self.nodes
                    }
                    self.return_node_sock.sendto(json.dumps(notification), (self.localhost, 1200))
            else:
                self.nodes = network
                self.logger.debug("Network updated: ntw: %s, ngh: %s" % (self.nodes, self.neighbors))

    def process_user_message(self, message):
        source = message['source_addr']
        dest = message['dest_addr']
        data = message['data']

        if self.localhost == dest:
            self.logger.info('Message received: %s' % data)
        else:
            route = bd_connect.consult_target(dest)
            self.send(route[0].get('next_hop'), message)


    def send(self, destination, message):
        try:
            message_bytes = json.dumps(message)
            self.aodv_sock.sendto(message_bytes, (destination, 1225))
        except Exception as e:
            self.logger.exception("[send] Message not sent due to") 

    def send_broadcast(self, message):
        try:
            self.aodv_brd_sock.sendto(json.dumps(message), ('255.255.255.255', 12345))
            self.logger.debug("Message %s broadcasted" % message)
        except Exception as e:
            self.logger.exception("[send_broadcast] Message not sent due to")

    def send_rreq(self, target, dest_sequence):
        self.logger.info("Finding route to %s" % target)
        self.src_sequence = self.src_sequence + 1
        self.broadcast_id = self.broadcast_id + 1

        message = {
                'type': "msg_rreq",
                'sender' : self.src_address,        
                'source_addr': self.src_address,
                'source_sequence': self.src_sequence,
                'broadcast_id': self.broadcast_id,
                'dest_addr':target,
                'dest_sequence': dest_sequence,
                'hop_cnt':self.hop_count
        }
        #SEND RREQ TO OWN NEIGHBORS
        self.send_broadcast(message)

    def forward_rreq(self, rreq_message):
        self.logger.debug("Forwarding...")
        rreq_dict = rreq_message

        message = {
                'type' : rreq_dict['type'],
                'sender' : self.localhost,    
                'source_addr' : rreq_dict['source_addr'],
                'source_sequence' : rreq_dict['source_sequence'],
                'broadcast_id' : rreq_dict['broadcast_id'],
                'dest_addr': rreq_dict['dest_addr'],
                'dest_sequence' : rreq_dict['dest_sequence'],
                'hop_cnt' : rreq_dict['hop_cnt']
        }

        #envio del mensaje en broadcast
        self.send_broadcast(message)

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
                bd_connect.update_routing_table(("target_seq_number", source_sequence, 'ID', rt_record[0].get("ID")))
            
            elif int(rt_record[0].get("target_seq_number")) == source_sequence:
                if rt_record[0].get("hop_count") > hop_count:
                    bd_connect.update_routing_table(("hop_count", hop_count, 'ID', rt_record[0].get("ID")))
                    bd_connect.update_routing_table(("next_hop", sender, 'ID', rt_record[0].get("ID")))

            elif int(rt_record[0].get("target_seq_number") == -1):
                bd_connect.update_routing_table(("target_seq_number", source_sequence, 'ID', rt_record[0].get("ID")))

        else:
            # If there's no route to destination, and originator is not the
            # same as node IP address, add entry
            if source_addr != self.localhost:
                bd_connect.insert_routing_table(routing_list)
                bd_connect.insert_rreq((source_addr, broadcast_id))

        # Check if localhost is the destination. If it is, generate and send an
        # RREP back.
        if (self.localhost == dest_addr): 
                self.send_rrep(source_addr, sender, dest_addr, dest_addr, 0, 0) 

        # Localhost is not the destination. Check if this node has a valid route
        # to the destination. If it does, generate and send back an
        # RREP.
        else:
            target = bd_connect.consult_target(dest_addr)
            self.logger.debug("[process_rreq] Target Record %s" % target)
            if (target):
                # Verify that the route is valid and has a higher seq number

                if target[0].get("target_seq_number") >=dest_sequence:
                        self.send_rrep(source_addr, sender, self.localhost, dest_addr, target[0].get("target_seq_number"), target[0].get("hop_count"))
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
            "source_addr" : int_node,
            "hop_cnt" : hop_count,
            "dest_addr" : target,
            "dest_sequence" : dest_seq
        }

        self.send(next_hop, message)

    def forward_rrep(self, message, next_hop):
        # There is no need to rebuild the whole RREP, only change
        # the sender IP Address
        self.logger.debug("Forwarding RREP...")
        message["sender"] = self.localhost
        self.send(next_hop, message)

    def process_rrep(self, message):
        self.logger.debug("Processing RREP message %s" %message)

        sender = message["sender"]
        source_addr = message["source_addr"]
        hop_count = int(message["hop_cnt"]) + 1
        message['hop_cnt'] = str(hop_count)
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
            record = bd_connect.consult_target(source_addr)
            if record:
                if record[0].get('hop_count') > hop_count:
                    bd_connect.insert_routing_table(routing_list)
            else:
                bd_connect.insert_routing_table(routing_list)
                                
            find_rt_end_time = time.time()
            final_time = find_rt_end_time - self.times_dict[source_addr]
            self.logger.info("Route to %s found in %s" % (source_addr, final_time))

            for msg in self.message_pend_list:
                self.logger.debug("[process_rrep] Evaluating: %s" % msg)
                if msg['dest_addr'] == source_addr:
                    next_hop = sender
                    self.send(next_hop, msg)
                    self.message_pend_list.remove(msg)
        else:
            record = bd_connect.consult_target(source_addr)
            if record:
                bd_connect.update_routing_table(('status', 1, 'ID', record[0].get('ID')))
                bd_connect.update_routing_table(('target_seq_number', dest_sequence, 'ID', record[0].get('ID')))
            else:
                bd_connect.insert_routing_table(routing_list)
            
            record = bd_connect.consult_target(dest_addr)
            self.forward_rrep(message, record[0].get('next_hop'))

    def send_rerr(self, target, dest_sequence, op_info):
        self.logger.debug("Send RERR")

        #INSTANCE RRER MESSAGE
        message = {
            'type':'msg_rerr',
            'sender': self.localhost,
            'dest_count':'1',
            'dest_sequence':int(dest_sequence) + 1,
            'dest_addr': target
        }

        # IF THERE IS AN ADDITIONAL UNREACHABLE NODE, APPEND ADDITIONAL INFO
        # TO THE RERR MESSAGE
        if op_info:
            message['op_info'] = op_info

        #SEND RERR TO OWN NEIGHBORS
        self.send_broadcast(message)

    def forward_rerr(self, message):
        self.logger.debug("Forwarding RERR...")

        message['sender'] = self.localhost

        self.send_broadcast(message)

    def process_rerr_message(self, message):
        self.logger.debug("Processing RERR message %s" % message)

        message_type = message['type']
        sender = message['sender']
        dest_addr = message['dest_addr']
        dest_sequence = message['dest_sequence']

        # IF THERE IS ADDINTIONAL INFO IN THE PACKET, PROCESS THIS FIRST
        if message.get('op_info'):
            additional_info = message.get('op_info')

            for rt in additional_info:
                route = bd_connect.consult_target(rt['dest_addr'])
                if route:
                    if route[0].get('next_hop') == sender:
                        bd_connect.update_routing_table(('status', 0, 'ID', route[0].get('ID')))

        # Process message only if there is an active route
        # to the destination where next hop IP address is the same
        # as the sender IP address in the packet received.

        target = bd_connect.consult_target(dest_addr)
        if target:
            if target[0].get('next_hop') == sender:
                bd_connect.update_routing_table(('status', 0, 'ID', target[0].get('ID')))
                self.forward_rerr(message)

    def process_neighbor_timeout(self, node):
        self.logger.debug("Timeout activated for %s" % node)

        target = bd_connect.consult_target(node)
        bd_connect.update_routing_table(('status', 0, 'ID', target[0].get('ID')))

        next_hop_list = bd_connect.consult_next_hop(node)
        route_nh_list = []

        for rt in next_hop_list:
            obj = {}
            obj['dest_addr'] = rt['target_address']
            obj['dest_sequence'] = rt['target_seq_number']

            route_nh_list.append(obj)

        # Send RERR
        self.send_rerr(node, target[0].get('target_seq_number'), route_nh_list)

    def send_hello_message(self):
        try:
            message_type = "msg_hello"
            sender = self.localhost
            message = {
                'type': message_type,
                'sender': sender
            }
            self.send_broadcast(message)

            # Restart the timer
            self.hello_timer.cancel()
            self.hello_timer = th.Timer(AODV_HELLO_INTERVAL, self.send_hello_message, ())
            self.hello_timer.start()
        except:
            pass

    def process_hello_message(self, message):
        sender = message['sender']
        try:
            if sender in self.neighbors.keys():
                ngh = self.neighbors[sender]
                timer = ngh['timer']
                timer.cancel()
                timer = th.Timer(
                    AODV_HELLO_TIMEOUT,
                    self.process_neighbor_timeout,
                    [sender]
                )

                self.neighbors[sender] = {
                    'neighbor': sender,
                    'timer': timer
                }

                timer.start()
            else:
                timer = th.Timer(
                    AODV_HELLO_TIMEOUT,
                    self.process_neighbor_timeout,
                    [sender]
                )

                self.neighbors[sender] ={
                    'neighbor': sender,
                    'timer': timer
                }

                timer.start()
                self.logger.debug("Neighbor added: %s" % sender)

                if bd_connect.consult_target(sender):
                    #RESTART ROUTE LIFETIME (PENDING)
                    pass
                else:
                    route = (
                        sender,     #Target
                        sender,     #Next_hop
                        1,          #Target sequence number
                        1,          #Hop count
                        1,          #Status
                        1,          #Lifetime
                    )
                    bd_connect.insert_routing_table(route)
                    
                    #RESTART ROUTE LIFETIME (PENDING)
        except:
            pass

    def receive(self):
        self.logger.debug("Receiving Thread ON!")
        while True:
            packet, (sender, _) = self.rcv_sock.recvfrom(1024)
            self.logger.debug("Packet received from %s" % sender)

            packet = json.loads(packet)
            if packet.get('sender') != self.localhost and packet.get('source_addr') != self.localhost:
                if packet.get('type') == 'msg_rreq':
                    self.process_rreq(packet)
                elif packet.get('type') == 'msg_hello':
                    self.process_hello_message(packet)
                elif packet.get('type') == 'msg_rerr':
                    self.process_rerr_message(packet)

    def unicast_listener(self):
        self.logger.debug("RREP listener ON!")
        while True:
            packet, (sender, _) = self.rrep_listen_sock.recvfrom(1024)
            self.logger.debug("Unicast Packet received from %s" % sender)

            packet = json.loads(packet)
            if packet.get('type') == 'msg_rrep':
                self.process_rrep(packet)
            elif packet.get('type') == 'notify':
                self.process_user_message(packet)

    def start(self):
        #CREATING SOCKETS
        self.neighbor_sock = socket(AF_INET, SOCK_DGRAM)
        self.neighbor_sock.bind((self.localhost, 1212))

        self.return_node_sock = socket(AF_INET, SOCK_DGRAM)

        self.aodv_sock = socket(AF_INET, SOCK_DGRAM)

        self.aodv_brd_sock = socket(AF_INET, SOCK_DGRAM)
        self.aodv_brd_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        self.rcv_sock = socket(AF_INET, SOCK_DGRAM)
        self.rcv_sock.bind(("", 12345))

        self.rrep_listen_sock = socket(AF_INET, SOCK_DGRAM)
        self.rrep_listen_sock.bind((self.localhost, 1225))

        #HELLO TIMER START
        self.hello_timer = th.Timer(AODV_HELLO_INTERVAL, self.send_hello_message)

        #CREATING THREADS
        neighbors = th.Thread(target = self.receive_nodes, name = self.receive_nodes)
        main_listen = th.Thread(target = self.receive, name = self.receive)
        rrep_listener = th.Thread(target = self.unicast_listener, name = self.unicast_listener)
        
        #STARTING THREADS
        neighbors.start()
        main_listen.start()
        rrep_listener.start()

        self.hello_timer.start()