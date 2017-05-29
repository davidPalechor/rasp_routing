import time
import zmq
import random

def consumer():
    try:
    	consumer_id = random.randrange(1,10005)
    	print "I am consumer #%s" % (consumer_id)
    	context = zmq.Context()
    	# recieve work
    	consumer_receiver = context.socket(zmq.PULL)
    	consumer_receiver.bind("tcp://192.168.0.195:5558")
    	# send work
    	consumer_sender = context.socket(zmq.PUSH)
    	consumer_sender.connect("tcp://192.168.0.210:5558")
    
    	while True:
            work = consumer_receiver.recv_json()
            data = work['num']
            print data 
            result = { 'consumer' : consumer_id, 'num' : data}
            consumer_sender.send_json(result)
    except KeyboardInterrupt:
	print "Hasta luego"

consumer()
