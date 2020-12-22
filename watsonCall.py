from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from threading import Thread
from ibm_watson.websocket import RecognizeCallback, AudioSource
from Assistant import assistant
from queue import Queue

# authenticate stt
apiKey = '63QDBci-JNp76iwczAz_nkEWxsa9q1ki494AozKmNJ58'  # Reed's S2T api key
credentialsUrl = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/fe323d86-f6b2-403e-b2a0-8504af25d34b'
dallasUrl = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com'

authenticator = IAMAuthenticator(apiKey)
speech_to_text = SpeechToTextV1(
    authenticator=authenticator
)
speech_to_text.set_service_url(dallasUrl)

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
                assistant_response = assistant(transcript)
                transcript_queue.put(transcript)
                transcript_queue.put(assistant_response)

            else:
                print("Interim transcript:", transcript)
        except Exception as e:
            print("Could not interpret data. Data: %s. Error: %s.", (data, e))

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
