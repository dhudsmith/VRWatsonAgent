from flask import Flask
from flask_sockets import Sockets
import watsonCall
from server.services import *
from Assistant import assistant

import sys, traceback
# import stt
from queue import Queue

app = Flask(__name__, template_folder='public/', static_folder='public/', static_url_path='')
sockets: Sockets = Sockets(app)

# buffer queue (main.py)
BUFFER_MAX_ELEMENT = 20
buffer_queue = Queue(maxsize=BUFFER_MAX_ELEMENT)

stt_dict = watsonCall.watson_streaming_stt(buffer_queue, content_type="audio/l16;rate=16000;channels=1")

# index
@app.route('/')
def hello_world():
    return app.send_static_file('newIndex.html') #index.html is normal site


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
    return app.send_static_file('404.html')


@app.errorhandler(500)
@app.route("/error500")
def requests_error(error):
    return app.send_static_file('500.html')

# socket
def stt(message):
    print("TODO: act upon this message")
    pass

# @app.route('/initialize_stt')
# def initialize_stt(audio_metadata):
    # parse audio metadata

    # initialize watson stt websocket (stt.py)
    # stt_dict = stt.watson_streaming_stt(buffer_queue, content_type="audio/l16;rate=%i" % RATE)

    pass

    # Stop stt - I might need this later
    # stt_dict["audio_source"].completed_recording()
    # stt_dict["stream_thread"].join()

@sockets.route('/api')
def api(socket):
    while True:
        try:
            message = socket.receive()
            if isinstance(message, bytearray):
                print("Got a bytearray from the client. Length:", len(message))
                # stt(message)
                # socket.send("Recieved bytearray. len(%i)" % len(message))
                # socket.send(message)

                buffer_queue.put(message)
                x = 1

                # transcript = stt(message)
                # intent = assistant(transcript)
                # socket.send(intent)
                # print(intent)
            else:
                print("Got this from the client:", message)
                socket.send(message)

                assistantmsg = assistant(message)
                print("Got this from the api assistant:", assistantmsg)
                socket.send(assistantmsg)

        except WebSocketError as e:
            print("WebSocketError:", e)
            traceback.print_exc(file=sys.stdout)
            break


initServices(app)

if __name__ == "__main__":
    app.debug = True

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    from geventwebsocket.exceptions import WebSocketError

    server = pywsgi.WSGIServer(("127.0.0.1", 5000), app, handler_class=WebSocketHandler, )
    server.serve_forever()
