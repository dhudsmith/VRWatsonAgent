from flask import Flask
from flask_sockets import Sockets

from server.services import *

import sys, traceback
import watsonCall

app = Flask(__name__, template_folder='public/', static_folder='public/', static_url_path='')

sockets: Sockets = Sockets(app)

# index
@app.route('/')
def hello_world():
    return app.send_static_file('index.html')


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
    return app.send_static_file('404.html')


@app.errorhandler(500)
@app.route("/error500")
def requests_error(error):
    return app.send_static_file('500.html')

@sockets.route('/api')
def api(socket):
    while True:
        try:
            message = socket.receive()
            if isinstance(message, bytearray):
                print("Got a bytearray from the client. Length:", len(message))
                transcript = watsonCall.sttCall(message)
                print(transcript)
                socket.send("Recieved bytearray. len(%i)" % len(message))
                socket.send(message)
            else:
                print("Got this from the client:", message)
                socket.send(message)

        except WebSocketError as e:
            print("WebSocketError:", e)
            traceback.print_exc(file=sys.stdout)
            break

# put in new file, make function to get transcript, use that function here instead of message
# message has the stuff I need

initServices(app)

if __name__ == "__main__":
    app.debug = True

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    from geventwebsocket.exceptions import WebSocketError

    server = pywsgi.WSGIServer(("127.0.0.1", 5000), app, handler_class=WebSocketHandler, )
    server.serve_forever()