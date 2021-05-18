# imports
import json
import os
import sys
import traceback
from queue import Queue
from threading import Thread
import websocket
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from transcript import Transcript

websocket.enableTrace(True)

# setup tts
tts_apikey = os.getenv('TTS_APIKEY')
serviceURL = os.getenv('TTS_SERVICEURL')

# setup stt
stt_apikey = os.getenv('STT_APIKEY')
dallasUrl = os.getenv('DALLAS_URL')

# setup assistant
assistant_apikey = os.getenv('ASSISTANT_APIKEY')
assistant_URL = os.getenv('ASSISTANT_ID')


class WatsonTTS:
    def __init__(self, audio_queue: Queue, apikey=tts_apikey, service_url=serviceURL, voice='en-US_KevinV3Voice'):
        """
        WatsonTTS handles all functionality of converting the current transcript text to audio

        :param audio_queue: queue to place the audio bytes
        :param voice: voice selection for the audio
        """
        # get tts token
        auth = IAMAuthenticator(apikey)

        self.voice = voice
        self.audio_queue = audio_queue

        self.wsURI = f"wss://{service_url}/v1/synthesize?access_token={auth.token_manager.get_token()}&voice={self.voice}"

        # the websocket object
        self.ws = websocket.WebSocket()

    def synthesize_speech_ws(self, text) -> Thread:
        """
        we will listen for messages on a separate thread
        receiving messages over the websocket involves waiting on
        a network data transfer. This releases the Global Interpreter
        Lock allowing the main thread to use the cpu to do other good
        things like process data received from previous messages. This
        function returns the thread object so that it can later be joined.
        :param text: The text to be spoken
        :return: the thread object which does the work of receiving audio chunks over the websocket
        """

        # TODO: check that authentication hasn't expired

        # connect to the websocket
        self.ws.connect(self.wsURI)

        # format message and send to TTS over the websocket
        message = json.dumps(dict(text=text, accept='audio/wav'))
        self.ws.send(message)

        # create the thread and start listening
        listen_thread = Thread(target=self.listen)
        listen_thread.start()

        return listen_thread

    def listen(self) -> None:
        """
        Receive new messages until the websocket closes. This stopping condition is sufficient
        because, according to the TTS docs, the websocket server will close the connection once
        the audio has finished sending.
        """

        while self.ws.connected:
            chunk = self.ws.recv()
            if isinstance(chunk, bytes):
                self.audio_queue.put(chunk)

    def synthesize_speech_to_file(self, text: str, filename: str) -> None:
        """
        This method streams audio chunks into a file as they are received over a websocket.
        For the Watson virtual agent, we will need a similar method that sends l16 audio over the python-unity websocket.

        :param text: The text to be spoken
        :param filename: The output file
        """

        listen_thread = self.synthesize_speech_ws(text)

        with open(filename, 'wb') as f:
            # This while loop continues to get messages from the audio_gueue. If these messages are bytes,
            # then they are written to the provided file. If they are string, they are printed to the console. When
            # Watson TTS completes the audio synthesis, it closes the websocket connection. In this case,
            # the while loop first "joins" the listen thread which pauses continued execution until thread completes.
            # This guarantees that all audio chunks have been put in the queue. After joining the thread,
            # any remaining messages are read from the queue and the while loop is exited.
            while True:
                print("Queue size:", self.audio_queue.qsize())
                # wait for thread to complete to make sure we get last chunks
                if not self.ws.connected and listen_thread.is_alive():
                    print("Websocket connection closed so joining thread.")
                    listen_thread.join()

                # exit if the thread is dead and the queue is empty
                if not listen_thread.is_alive() and self.audio_queue.qsize() == 0:
                    print("Thread dead and queue empty so breaking out of loop.")
                    break

                # get the audio and write to a file if it is bytes
                chunk = self.audio_queue.get()
                if isinstance(chunk, bytes):
                    f.write(chunk)
                    print(f"Wrote chunk of {len(chunk)} bytes.")
                # otherwise just print it
                elif isinstance(chunk, str):
                    print(chunk)

    def synthesize_speech_to_byte_array(self, text: str) -> None:

        listen_thread = self.synthesize_speech_ws(text)

        while True:
            print("Queue size:", self.audio_queue.qsize())
            # wait for thread to complete to make sure we get last chunks
            if not self.ws.connected and listen_thread.is_alive():
                print("Websocket connection closed so joining thread.")
                listen_thread.join()
                break









# transcript buffer
BUFFER_MAX_ELEMENT = 20
transcript_queue = Queue(maxsize=BUFFER_MAX_ELEMENT)


class WatsonSTT:
    def __init__(self, buffer_queue: Queue, content_type: str, transcript: Transcript):
        """
        Type some stuff about the class
        :param buffer_queue: a queue of audio bytes to be processed by speech to text
        :param content_type: a classifier for the Watson speech to text call
        :param transcript: an instance of the transcript class that contains the default values

        defines:
            current_transcript: an instance of the transcript class that will contain all info about the
                                current speech to text conversion

        """
        authenticator = IAMAuthenticator(stt_apikey)
        self.speech_to_text = SpeechToTextV1(
            authenticator=authenticator
        )
        self.speech_to_text.set_service_url(dallasUrl)
        self.current_transcript = transcript
        self.stream = self.watson_streaming_stt(buffer_queue, content_type)

    class MyRecognizeCallback(RecognizeCallback):
        def __init__(self, transcript):
            """
            MyRecognizeCallback expands on the Watson RecognizeCallback class

            This class should only be used within watsonSTT

            :param transcript: an instance of the transcript class that will keep track of the current
                                speech to text conversion
            """
            RecognizeCallback.__init__(self)
            self.classTranscript = transcript

        def on_data(self, data):
            """
            on_data stores the final results of Watson Speech to Text calls into the instance of the transcript class
            """
            try:
                results = data['results'][0]
                transcript = results['alternatives'][0]['transcript']
                if results["final"]:
                    self.classTranscript.originalMessage = transcript
                else:
                    print("Interim transcript:", transcript)
            except Exception as e:
                print("Could not interpret data. Data: %s. Error: %s." % (data, e))
                traceback.print_exc(file=sys.stdout)

        def on_error(self, error):
            print('Error received: {}'.format(error))

        def on_inactivity_timeout(self, error):
            print('Inactivity timeout: {}'.format(error))

    def watson_streaming_stt(self, buffer_queue, content_type) -> dict:
        """
        watson_streaming_stt starts a thread and begins processing the audio data in the buffer_queue in
            the thread

        :param buffer_queue: a queue of audio bytes to be processed by speech to text
        :param content_type: a classifier used by Watson Speech to Text call
        :return: a dictionary of the audio source and newly created thread
        """
        audio_source = AudioSource(buffer_queue, True, True)
        callback = self.MyRecognizeCallback(self.current_transcript)
        stt_stream_thread = Thread(
            target=self.speech_to_text.recognize_using_websocket,
            kwargs=dict(
                audio=audio_source,
                content_type=content_type,
                recognize_callback=callback,
                model='en-US_BroadbandModel',
                interim_results=False,
                max_alternatives=1)
        )
        stt_stream_thread.start()
        return {'audio_source': audio_source,
                'stream_thread': stt_stream_thread}

    def close_connection(self):
        """
        closes the connection to Watson and closes the thread
        can only be called after watson_streaming_stt has created the thread
        """
        self.stream["audio_source"].completed_recording()
        self.stream["stream_thread"].join()


class Assistant:
    def __init__(self):
        """
        Assistant handles answering the original message with the assistant response
        """

        # authenticate
        authenticator = IAMAuthenticator(assistant_apikey)
        self.assistant = AssistantV2(
            version='2020-04-01',
            authenticator=authenticator,
        )

        # create a session
        response = self.assistant.create_session(
            assistant_id=assistant_URL
        ).get_result()
        self.session_id = response['session_id']

    def message(self, text: str, timestep: str):
        """
        message creates the answer to the original question and returns it as a string

        :param text: message to answer
        :param timestep: 
        :return: the textual answer to the original question, <NO RESPONSE> if no answer
        """

        # structure input
        input = {
            'message_type': 'text',
            'text': text
        }

        # structure the context
        context = {
            'skills': {
                'main skill': {
                    'user_defined': {
                        'Bob_state': timestep
                    }
                }
            }
        }

        response = self.assistant.message(
            assistant_id=assistant_URL,
            session_id=self.session_id,
            input=input,
            context=context
        ).get_result()

        try:
            return str(response["output"]['generic'][0]['text'])
        except Exception:
            return "<NO RESPONSE>"
