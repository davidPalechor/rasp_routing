#!/usr/bin/python
import threading as th
import get_ip_address as gip
from socket import *
import routing as rt
import logging

class NeighborDiscovery(th.Thread):
    def __init__(self):
        th.Thread.__init__(self)
        self.neighbors = []
        self.ip_address = gip.get_lan_ip()
        self.logger = logging.getLogger(__name__)

    def broadcast(self, msg):
        self.logger.debug("Broadcasting '%s'" % msg)
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        s.sendto(msg, ('<broadcast>', 1200))

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def send_neighbors_to_aodv(self):
        self.logger.debug("Sending to AODV module '%s'" % str(self.neighbors))
        s = socket(AF_INET, SOCK_DGRAM)
        s.sendto(str(self.neighbors), (self.ip_address, 1212))

    def notify_neighbors(self):
        th.Timer(60, self.notify_neighbors).start()
        self.logger.debug("Notifying neighbors")
        self.send_neighbors_to_aodv()

    def resend_neighbors(self,neighbors):
        new_neighbor = 0
        for addr in neighbors:
            if addr not in self.neighbors and addr != self.ip_address:
                self.add_neighbor(addr)
                new_neighbor += 1
        self.logger.debug("My Neighbors are: %s"%self.neighbors)
        return new_neighbor

    def listener(self):
        s = socket(AF_INET, SOCK_DGRAM)

        # SOCKET BINDING
        s.bind(('', 1200))
        while True:
            (packet, neighbor) = s.recvfrom(1024)

            if neighbor[0] != self.ip_address:
                if packet == "First message!":
                    self.add_neighbor(neighbor[0])
                    self.broadcast(str(self.neighbors))

                elif self.resend_neighbors(eval(packet) + [neighbor[0]]) > 0:
                    self.broadcast(str(self.neighbors))

    def run(self):
        self.logger.info("Listener ON %s" % self.ip_address)
        self.broadcast("First message!")
        self.notify_neighbors()
        self.listener()