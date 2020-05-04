from flask import Flask
from flask_sockets import Sockets

from server.services import *

import json

app = Flask(__name__, template_folder='public/', static_folder='public/', static_url_path='')

sockets = Sockets(app)


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


# socket
@sockets.route('/api')
def api(socket):
    while True:
        message = socket.receive()
        socket.send(message)
        #data = json.loads(message)
        # with open('appliances.json', 'r') as json_file:
        #     appliances = json.load(json_file)
        # appliances[data['device']] = data['capacity']
        # with open('appliances.json', 'w') as json_file:
        #     json.dump(appliances, json_file)


initServices(app)

if __name__ == "__main__":
    app.debug = True

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(("127.0.0.1", 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
