from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from threading import Thread
from ibm_watson.websocket import RecognizeCallback, AudioSource
from Assistant import Assistant
from queue import Queue
import os
import sys
import traceback

# setup stt
stt_apikey = os.getenv('STT_APIKEY')
dallasUrl = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com'

authenticator = IAMAuthenticator(stt_apikey)
speech_to_text = SpeechToTextV1(
    authenticator=authenticator
)
speech_to_text.set_service_url(dallasUrl)

# setup assistant
assistant = Assistant(apikey=os.getenv('ASSISTANT_APIKEY'),
                      assistant_id=os.getenv('ASSISTANT_ID'))

# transcript buffer
BUFFER_MAX_ELEMENT = 20
transcript_queue = Queue(maxsize=BUFFER_MAX_ELEMENT)


class MyRecognizeCallback(RecognizeCallback):
    def __init__(self):
        RecognizeCallback.__init__(self)

    def on_data(self, data):  # why is the transcript not showing up in on-data
        try:
            results = data['results'][0]
            transcript = results['alternatives'][0]['transcript']
            if results["final"]:
                assistant_response = assistant.message(transcript, 'TS1')
                transcript_queue.put(transcript)
                transcript_queue.put(assistant_response)
            else:
                print("Interim transcript:", transcript)
        except Exception as e:
            print("Could not interpret data. Data: %s. Error: %s." % (data, e))
            traceback.print_exc(file=sys.stdout)

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))


def watson_streaming_stt(buffer_queue, content_type):
    audio_source = AudioSource(buffer_queue, True, True)
    callback = MyRecognizeCallback()
    stt_stream_thread = Thread(
        target=speech_to_text.recognize_using_websocket,
        kwargs=dict(
            audio=audio_source,
            content_type=content_type,
            recognize_callback=callback,
            model='en-US_BroadbandModel',
            interim_results=False,
            max_alternatives=1)
    )
    stt_stream_thread.start()

    # return everything needed by main script
    return {'audio_source': audio_source,
            'stream_thread': stt_stream_thread}


def pop_transcript_queue():
    transcript = []
    while transcript_queue.qsize() > 0:
        transcript.append(transcript_queue.get())
    return transcript
