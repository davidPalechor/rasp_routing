#!/usr/bin/python
from aodv_protocol import AODV_Protocol
import json
import threading as th
import get_ip_address as gip
from socket import *
import routing as rt
import logging

AODV_HELLO_TIMEOUT = 30

class NodeDiscovery(th.Thread):
    def __init__(self):
        th.Thread.__init__(self)
        self.nodes = []
        self.neighbors = {}
        self.ip_address = gip.get_lan_ip()
        self.logger = logging.getLogger(__name__)
        self.aodv_obj = AODV_Protocol()

    def broadcast(self, msg):
        self.logger.debug("Broadcasting '%s'" % msg)
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        s.sendto(msg, ('<broadcast>', 1200))

    def add_node(self, node):
        self.nodes.append(node)
    
    def add_neighbor(self, node):
        if not node in self.neighbors:
            timer = th.Timer(AODV_HELLO_TIMEOUT,
                self.aodv_obj.process_neighbor_timeout,
                [node])

            self.neighbors[node] = {
                'neighbor': node,
                'timer': timer
            }

            timer.start()

    def send_nodes_to_aodv(self):
        self.logger.debug("Sending network to AODV module: ntw: '%s', ngh: %s" % (self.nodes, self.neighbors))
        network = {
            'nodes': self.nodes,
            'neighbors': self.neighbors
        }

        response = self.aodv_obj.receive_nodes(network)
        if response:
            self.logger.debug("Nodes have changed")
            self.nodes = response['nodes']
            self.neighbors = response['neighbors']

    def notify_nodes(self):
        th.Timer(60, self.notify_nodes).start()
        self.logger.debug("Notifying nodes")
        self.send_nodes_to_aodv()

    def resend_nodes(self,nodes):
        new_node = 0
        for addr in nodes:
            if addr not in self.nodes and addr != self.ip_address:
                self.add_node(addr)
                new_node += 1
        self.logger.debug("My Nodes are: %s"%self.nodes)
        return new_node

    def listener(self):
        s = socket(AF_INET, SOCK_DGRAM)

        # SOCKET BINDING
        s.bind(('', 1200))
        while True:
            (packet, node) = s.recvfrom(1024)
            if node[0] != self.ip_address:
                
                self.add_neighbor(node[0])
                if packet == "First message!":
                    self.add_node(node[0])
                    self.broadcast(str(self.nodes))

                elif self.resend_nodes(eval(packet) + [node[0]]) > 0:
                    self.broadcast(str(self.nodes))

    def run(self):
        self.logger.info("Listener ON %s" % self.ip_address)
        self.broadcast("First message!")
        self.notify_nodes()
        self.listener()