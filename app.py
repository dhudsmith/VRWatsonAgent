from flask import Flask
from flask_sockets import Sockets
import watsonCall

import sys, traceback
from queue import Queue
import json

app = Flask(__name__, template_folder='public/', static_folder='public/', static_url_path='')
sockets: Sockets = Sockets(app)

# index
@app.route('/')
def hello_world():
    return app.send_static_file('newIndex.html')  # index.html is normal site


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
    return app.send_static_file('404.html')


@app.errorhandler(500)
@app.route("/error500")
def requests_error(error):
    return app.send_static_file('500.html')


@sockets.route('/api')
def api(socket: Sockets.__name__):
    # buffer queue (main.py)
    BUFFER_MAX_ELEMENT = 20
    buffer_queue = Queue(maxsize=BUFFER_MAX_ELEMENT)
    stt_dict = watsonCall.watson_streaming_stt(buffer_queue, content_type="audio/l16;rate=16000;channels=1")

    while True:
        try:
            message = socket.receive()
            if isinstance(message, bytearray):
                buffer_queue.put(message)
            elif isinstance(message, str):
                try:
                    msg_dict = json.loads(message)
                    print(msg_dict)

                    if msg_dict['type'] == 'action':
                        if msg_dict['note'] == 'INITIATE':
                            pass  # setup stt here
                        elif msg_dict['note'] == 'STOP_LISTENING':
                            # gracefully close stt service
                            stt_dict["audio_source"].completed_recording()
                            stt_dict["stream_thread"].join()
                except Exception as e:
                    print("The message could not be interpreted. "
                          "Taking no action. Message: %s. Error: %s." % (message, e))

        except WebSocketError as e:
            print("WebSocketError:", e)
            traceback.print_exc(file=sys.stdout)
            break

if __name__ == "__main__":
    app.debug = True

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    from geventwebsocket.exceptions import WebSocketError

    server = pywsgi.WSGIServer(("127.0.0.1", 5000), app, handler_class=WebSocketHandler, )
    server.serve_forever()
