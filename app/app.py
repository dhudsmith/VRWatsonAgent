# imports
import os.path
import sys
import traceback
from queue import Queue
from typing import List

from flask import Flask
from flask_sockets import Sockets

import watsonCall
from watsonTTS import watsonTTS
from SocketMessage import SocketMessage

# get environmental variables


apikey = os.getenv('ASSISTANT_APIKEY')
assistant_id = os.getenv('ASSISTANT_ID')

app = Flask(__name__, template_folder='public/', static_folder='public/', static_url_path='')
sockets: Sockets = Sockets(app)


# index
@app.route('/')
def hello_world():
    return 'Hello World!'


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
    return "404 not found"


@app.errorhandler(500)
@app.route("/error500")
def requests_error(error):
    return "500 internal error"


@sockets.route('/api')
def api(socket: Sockets.__name__):
    # buffer queue (main.py)
    BUFFER_MAX_ELEMENT = 20
    buffer_queue = Queue(maxsize=BUFFER_MAX_ELEMENT)
    content_type = None
    stt_dict = None

    while True:
        try:
            message = socket.receive()
            if isinstance(message, bytearray):
                buffer_queue.put(message)
            elif isinstance(message, str):
                try:
                    msg = SocketMessage.from_json(message)
                    if msg.type == 'action':

                        print("Received %s message." % msg.note)
                        # INITIATE
                        if msg.note == 'INITIATE':
                            # setup stt here
                            content_type = msg.meta['format'] + \
                                           ";rate=" + msg.meta['freq'] + \
                                           ";channels=" + msg.meta['channel']

                        # START LISTENING
                        elif msg.note == 'START_LISTENING':
                            if content_type:
                                stt_dict = watsonCall.watson_streaming_stt(buffer_queue, content_type=content_type)
                            else:
                                print("Content type has not been specified. INITIATE may not have been called yet.")

                        # STOP LISTENING
                        elif msg.note == 'STOP_LISTENING':
                            # gracefully close stt service
                            if stt_dict:
                                stt_dict["audio_source"].completed_recording()
                                stt_dict["stream_thread"].join()

                            # Send final user & assistant transcript to web server
                            transcript = watsonCall.pop_transcript_queue()
                            if transcript:
                                print("You: " + transcript[0])
                                print("Assistant: " + transcript[1])

                                # new tts call
                                #voiceResponse = watsonTTS(transcript[1])
                                #voiceResponse.callSpeech()

                                # send results back over websocket
                                send_response(transcripts=transcript)

                except Exception as e:
                    traceback.print_exc(file=sys.stdout)
                    print("The message could not be interpreted. "
                          "Taking no action. Message: %s. Error: %s." % (message, e))
        except WebSocketError as e:
            print("WebSocketError:", e)
            traceback.print_exc(file=sys.stdout)
            break


def send_response(transcripts: List):
    msg_speech = SocketMessage(message_type="AGENT_RESULT", note='SPEAKER_TRANSCRIPT', meta={'text': transcripts[0]})
    msg_response = SocketMessage(message_type="AGENT_RESULT", note='AGENT_RESPONSE',  meta={'text': transcripts[1],
                                                                                            'intent': None})

    # TODO: why sending to all clients?
    for client in server.clients.values():
        client.ws.send(msg_speech.to_json())
        client.ws.send(msg_response.to_json())


if __name__ == "__main__":
    app.debug = True

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    from geventwebsocket.exceptions import WebSocketError

    # set the port dynamically with a default of 5000 for local development
    port = int(os.getenv('PORT', '5000'))

    print("Starting server at http://localhost:{port}".format(port=port))
    server = pywsgi.WSGIServer(("0.0.0.0", port), app, handler_class=WebSocketHandler, )
    server.serve_forever()
