import time
import zmq
import pprint

def result_collector():
    try:
    	context = zmq.Context()
    	results_receiver = context.socket(zmq.PULL)
    	results_receiver.bind("tcp://192.168.0.210:5558")
    	#collecter_data = {}
    	while True:
            result = results_receiver.recv_json()
            print result['consumer']
    except KeyboardInterrupt:
	print "Hasta Luego"

result_collector()
