from socket import *
import threading
import time

class PingerThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run (self):
        for i in range(10):
          print 'start thread'
          cs = socket(AF_INET, SOCK_DGRAM)
          cs.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
          cs.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
          cs.sendto('This is a test', ('10.20.161.66', 4499))
          time.sleep(1)

a = PingerThread() 
a.start()


cs = socket(AF_INET, SOCK_DGRAM)
try:
    cs.bind(('10.20.161.66', 4499))
except:
    print 'failed to bind'
    cs.close()
    raise
    cs.blocking(0)
data = cs.recvfrom(1024) # <-- waiting forever
print data