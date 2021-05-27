# imports
import os.path
import sys
import traceback
from queue import Queue

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
    voice_response = WatsonTTS(response_queue)

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

                            numBytes = 0
                            # Send final user & assistant transcript to web server
                            if current_transcript.originalMessage is not None:

                                # get assistant response
                                current_transcript.assistantResponse = assistant.message(
                                    current_transcript.originalMessage,
                                    'TS1')

                                print("You: " + current_transcript.originalMessage)
                                print("Assistant: " + current_transcript.assistantResponse)

                                # check for assistant response to message
                                if current_transcript.assistantResponse != '<NO RESPONSE>':
                                    # tts over Web Socket
                                    numBytes = voice_response.synthesize_speech_over_web_socket(
                                        current_transcript.assistantResponse,
                                        socket)

                            # send results back over websocket
                            print("Sending Transcript")
                            send_transcript(transcripts=current_transcript)
                            current_transcript = Transcript(None, None)
                            print("Sending Completed message signal")
                            send_done_synthesis_message(numBytes)

                except Exception as e:
                    traceback.print_exc(file=sys.stdout)
                    print("The message could not be interpreted. "
                          "Taking no action. Message: %s. Error: %s." % (message, e))
        except WebSocketError as e:
            print("WebSocketError:", e)
            traceback.print_exc(file=sys.stdout)
            break


def send_transcript(transcripts: Transcript):
    """
    Sends the transcript over the websocket to the client
    :param transcripts: instance of transcript class that contains the current transaction
    """
    msg_speech = SocketMessage(message_type="AGENT_RESULT", note='SPEAKER_TRANSCRIPT',
                               meta={'text': transcripts.originalMessage})
    msg_response = SocketMessage(message_type="AGENT_RESULT", note='AGENT_RESPONSE',
                                 meta={'text': transcripts.assistantResponse, 'intent': None})

    # TODO: why sending to all clients?
    for client in server.clients.values():
        client.ws.send(msg_speech.to_json())
        client.ws.send(msg_response.to_json())


def send_done_synthesis_message(num_bytes: int):
    """
    Sends message to client that TTS synthesis is complete
    :param num_bytes: the integer number of bytes sent over the websocket
    """
    msg_done = SocketMessage(message_type="action", note='DONE_SPEECH_SYNTHESIS',
                             meta={'bytes': num_bytes})

    # TODO: why sending to all clients?
    for client in server.clients.values():
        client.ws.send(msg_done.to_json())


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
