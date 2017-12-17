#!/usr/bin/python
from find_neighbours import NeighborDiscovery
import logging
import logging.config
import os

def main():
    logging.basicConfig(filename="logs/aodv.log", 
                        level=logging.DEBUG,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    logger = logging.getLogger("main")

    logger.info("Main triggered!")

    ngh_find = NeighborDiscovery()
    ngh_find.start()
    
if __name__ == "__main__":
    main()