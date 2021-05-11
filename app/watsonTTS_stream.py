from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import websocket
import os
import json
from threading import Thread
from queue import Queue

websocket.enableTrace(True)


class WatsonTTS:
    def __init__(self, apikey, service_url, audio_queue: Queue, voice='en-US_KevinV3Voice'):
        """

        :param apikey:
        :param service_url:
        :param audio_queue:
        :param voice:
        """
        # get tts token
        auth = IAMAuthenticator(tts_apikey)

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
            self.audio_queue.put(self.ws.recv())

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
                print("Queue size:", audio_queue.qsize())
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


if __name__ == '__main__':
    # setup tts
    tts_apikey = os.getenv('TTS_APIKEY')
    service_url = os.getenv('TTS_SERVICEURL')

    # queue for processing audio
    audio_queue = Queue(100)
    tts = WatsonTTS(tts_apikey, service_url, audio_queue)

    # generate some audio and write to file
    text = """Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in
    Liberty, and dedicated to the proposition that all men are created equal."""
    tts.synthesize_speech_to_file(text, '../assets/audio/websocket_test_1.wav')

    # gen some more audio
    text2 = """Now we are engaged in a great civil war, testing whether that nation, or any nation so conceived and so
    dedicated, can long endure. We are met on a great battle-field of that war. We have come to dedicate a
    portion of that field, as a final resting place for those who here gave their lives that that nation might
    live. It is altogether fitting and proper that we should do this."""
    tts.synthesize_speech_to_file(text2, '../assets/audio/websocket_test_2.wav')
