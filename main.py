#!/usr/bin/python
from find_neighbours import NeighborDiscovery
from aodv_protocol import AODV_Protocol
import logging
import logging.config
import os
import threading as th 

def send_message_demon(aodv_obj):
    th.Timer(120, send_message_demon, [aodv_obj]).start()
    logger = logging.info("Sending message")
    aodv_obj.send("State Change!")

def main():

    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create file handler which logs even debug messages
    fh = logging.FileHandler('spam.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("Main triggered!")

    ngh_find = NeighborDiscovery()
    ngh_find.start()

    aodv = AODV_Protocol()
    aodv.start()
    send_message_demon(aodv)
    
if __name__ == "__main__":
    main()