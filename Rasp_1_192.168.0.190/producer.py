import time
import zmq

def producer():
    context = zmq.Context()
    zmq_socket = context.socket(zmq.PUSH)
    zmq_socket.bind("tcp://192.168.0.190:5557")
    # Start your result manager and workers before you start your producers
    work_message = {'num' : 'Hola mundo'}
    zmq_socket.send_json(work_message)

producer()
