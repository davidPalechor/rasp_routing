#!/usr/bin/python
from find_neighbours import NeighborDiscovery
from aodv_protocol import AODV_Protocol
import logging
import logging.config
import os
import threading as th 

def send_message_demon(aodv_obj):
    th.Timer(120, send_message_demon, [aodv_obj]).start()
    logger = logging.debug("Sending message")
    aodv_obj.send("State Change!")

def main():
    # logging.basicConfig(filename="logs/aodv.log", 
    #                     level=logging.DEBUG,
    #                     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.basicConfig(level=logging.DEBUG,
                        format="[%(asctime)s - %(name)s] - %(levelname)s - %(message)s")

    logger = logging.getLogger("main")

    logger.debug("Main triggered!")

    ngh_find = NeighborDiscovery()
    ngh_find.start()

    aodv = AODV_Protocol()
    aodv.start()
    send_message_demon(aodv)
    
if __name__ == "__main__":
    main()