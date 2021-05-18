# imports
import os.path
import socket
import sys
import traceback
from queue import Queue
from typing import List

from flask import Flask
from flask_sockets import Sockets

from watsonUtilities import WatsonTTS, WatsonSTT, Assistant
from transcript import Transcript
from SocketMessage import SocketMessage

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
    response_queue = Queue()
    content_type = None
    stt_dict = None
    current_transcript = Transcript(None, None)
    assistant = Assistant()
    voice_response = None
    byte_response_queue = Queue()

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
                                stt_dict = WatsonSTT(buffer_queue, content_type, current_transcript)
                            else:
                                print("Content type has not been specified. INITIATE may not have been called yet.")

                        # STOP LISTENING
                        elif msg.note == 'STOP_LISTENING':
                            # gracefully close stt service
                            if stt_dict:
                                stt_dict.close_connection()

                            # get assistant response
                            current_transcript.assistantResponse = assistant.message(current_transcript.originalMessage,
                                                                                     'TS1')

                            # Send final user & assistant transcript to web server
                            if current_transcript.originalMessage is not None:
                                print("You: " + current_transcript.originalMessage)
                                print("Assistant: " + current_transcript.assistantResponse)

                                # tts call
                                voice_response = WatsonTTS(response_queue)
                                # tts to byte array
                                voice_response.synthesize_speech_to_byte_array(current_transcript.assistantResponse)

                                # file tts for testing
                                # voice_response.synthesize_speech_to_file(current_transcript.assistantResponse,
                                #                                  '../assets/audio/TEST.wav')

                                # send results back over websocket
                                # TODO
                                send_transcript(transcripts=current_transcript)
                                current_transcript = Transcript(None, None)

                            if voice_response is not None:
                                while response_queue.qsize() > 0:
                                    print(f"queue size: {(response_queue.qsize())}")
                                    send_byte_array(response_queue.get())

                                send_done_synthesis_message()

                except Exception as e:
                    traceback.print_exc(file=sys.stdout)
                    print("The message could not be interpreted. "
                          "Taking no action. Message: %s. Error: %s." % (message, e))
        except WebSocketError as e:
            print("WebSocketError:", e)
            traceback.print_exc(file=sys.stdout)
            break


def send_transcript(transcripts: Transcript):
    msg_speech = SocketMessage(message_type="AGENT_RESULT", note='SPEAKER_TRANSCRIPT',
                               meta={'text': transcripts.originalMessage})
    msg_response = SocketMessage(message_type="AGENT_RESULT", note='AGENT_RESPONSE',
                                 meta={'text': transcripts.assistantResponse, 'intent': None})

    # TODO: why sending to all clients?
    for client in server.clients.values():
        client.ws.send(msg_speech.to_json())
        client.ws.send(msg_response.to_json())


def send_done_synthesis_message():
    """
    Sends message to client that TTS synthesis is complete
    """
    msg_done = SocketMessage(message_type="action", note='DONE_SPEECH_SYNTHESIS',
                             meta={'text': 'dont break?'})

    # TODO: why sending to all clients?
    for client in server.clients.values():
        client.ws.send(msg_done.to_json())


def send_byte_array(chunk: bytearray):
    for client in server.clients.values():
        client.ws.send(chunk)


if __name__ == "__main__":
    app.debug = True

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    from geventwebsocket.exceptions import WebSocketError

    # set the port dynamically with a default of 5000 for local development
    port = int(os.getenv('PORT', '5000'))

    print(f"Starting server at http://localhost:{port}")
    server = pywsgi.WSGIServer(("0.0.0.0", port), app, handler_class=WebSocketHandler)
    server.serve_forever()
