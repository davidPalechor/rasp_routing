#!/usr/bin/python
import threading as th
import get_ip_address as gip
from socket import *
import routing as rt

class NeighborDiscovery(th.Thread):
    def __init__(self):
        th.Thread.__init__(self)
        self.neighbors = []
        self.ip_address = gip.get_lan_ip()

    def broadcast(self, msg):
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        s.sendto(msg, ('255.255.255.255', 1200))

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def resend_neighbors(self,neighbors):
        new_neighbor = 0
        for addr in neighbors:
            if addr not in self.neighbors and addr != self.ip_address:
                self.add_neighbor(addr)
                new_neighbor += 1
        print "My Neighbors are: %s"%self.neighbors
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
        print "Listener ON!"
        self.broadcast("First message!")
        self.listener()