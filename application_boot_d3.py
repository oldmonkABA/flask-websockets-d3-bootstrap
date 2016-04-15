"""
Demo Flask application to test the operation of Flask with socket.io
Aim is to create a webpage that is constantly updated with random numbers from a background python process.
30th May 2014
"""
#from gevent import monkey
#monkey.patch_all()
# Start with a basic flask app webpage.

import eventlet
eventlet.monkey_patch()
from flask.ext.socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context,request
from random import random
from time import sleep
from threading import Thread, Event


__author__ = 'aba'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

#turn the flask app into a socketio app
socketio = SocketIO(app, async_mode='eventlet',engineio_logger=True)

#random number Generator Thread
thread = Thread()
thread_stop_event = Event()

class RandomThread(Thread):
    def __init__(self,maxn):
        self.delay = 1.0
        self.max=maxn
        super(RandomThread, self).__init__()

    def randomNumberGenerator(self):
        """
        Generate a random number every 1 second and emit to a socketio instance (broadcast)
        Ideally to be run in a separate thread?
        """
        #infinite loop of magical random numbers
        print "Making random numbers"
        i=1
        while not thread_stop_event.isSet():
            number = self.max*round(random(), 3)
            print number
            socketio.emit('newnumber', {'number': number,'ind':i}, namespace='/test')
            sleep(self.delay)
            i+=1

    def run(self):
        self.randomNumberGenerator()


@socketio.on("channel-a",namespace='/test')
def channel_a(message):
    '''
    Receives a message, on `channel-a`, and emits to the same channel.
    '''
    print "[x] Received\t: ", message

    server_message = "Hi Client, I am the Server."
    emit("channel-a", {'data':server_message})
    print "[x] Sent\t: ", server_message

@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('sockets_d3_boot.html')

@socketio.on('start_gen', namespace='/test')
def start_gen_numbers(message):
    # need visibility of the global thread object
    maxn = int(message['data']) 
    print maxn
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print "Starting Thread"
        thread = RandomThread(maxn)
        thread.daemon = True
        thread.start()

@socketio.on('connect',namespace='/test')
def test_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    thread_stop_event.set()
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
