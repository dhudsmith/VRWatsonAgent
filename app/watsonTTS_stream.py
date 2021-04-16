from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import websocket
websocket.enableTrace(True)
import os, json
from threading import Thread
from queue import Queue


class watsonTTS:
    def __init__(self, tts_apikey, service_url, audio_queue: Queue, voice='en-US_KevinV3Voice'):
        # get tts token
        auth = IAMAuthenticator(tts_apikey)

        self.voice = voice
        self.audio_queue = audio_queue

        self.wsURI = f"wss://{service_url}/v1/synthesize?access_token={auth.token_manager.get_token()}&voice={self.voice}"
        # establish the websocket connection
        self.ws = websocket.WebSocket()
        self.ws.connect(self.wsURI)

        self.listen_thread = Thread(target=self.listen)
        self.listen_thread.start()

    def synthesize_speech_ws(self, text):
        message = json.dumps(dict(text=text, accept='audio/wav'))
        self.ws.send(message)

    def listen(self):
        while self.ws.connected:
            self.audio_queue.put(self.ws.recv())



if __name__ == '__main__':

    # setup tts
    tts_apikey = os.getenv('TTS_APIKEY')
    service_url = os.getenv('TTS_SERVICEURL')

    #queue for processing audio
    audio_queue = Queue(10)
    tts = watsonTTS(tts_apikey, service_url, audio_queue)

    # generate some audio and write to file
    text = \
    """
    Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in
    Liberty, and dedicated to the proposition that all men are created equal.
    """

    tts.synthesize_speech_ws(text)

    # in this example, we will stream the audio into a file, but you could equally well pass the chunks along
    # to a client application for playback
    with open('audio.wav', 'wb') as f:
        while True:
            # wait for thread to complete to make sure we get last chunks
            if not tts.ws.connected:
                tts.listen_thread.join()

            # get the audio and write to a file if it is bytes
            chunk = audio_queue.get()
            if isinstance(chunk, bytes):
                f.write(chunk)
                print(f"Wrote chunk of {len(chunk)} bytes.")
            elif isinstance(chunk, str):
                print(chunk)

            # break out of the while loop
            if not tts.ws.connected:
                break





