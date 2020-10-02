from os.path import join, dirname
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import json

# authenticate stt
apiKey = '63QDBci-JNp76iwczAz_nkEWxsa9q1ki494AozKmNJ58' # Reed's S2T api key
credentialsUrl = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/fe323d86-f6b2-403e-b2a0-8504af25d34b'
dallasUrl = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com'

authenticator = IAMAuthenticator(apiKey)
speech_to_text = SpeechToTextV1(
    authenticator=authenticator
)
speech_to_text.set_service_url(dallasUrl)

# Watson S2T Code
# pip install ibm_watson
def sttCall(audio):
    speech_recognition_results = speech_to_text.recognize(
        audio=audio,
        content_type='audio/l16;rate=16000;channels=1',
        # rate = 22050, # TODO: pass as argument
        # channels = 1, # TODO: pass as argument
        word_alternatives_threshold=0.3,
        speaker_labels=False
    ).get_result()

    transcript = []
    for i in speech_recognition_results['results']:
        text = i['alternatives'][0]['transcript']
        transcript.append(text)

    return transcript


# new stuff - speech recognition function
from threading import Thread
from ibm_watson.websocket import RecognizeCallback, AudioSource

class MyRecognizeCallback(RecognizeCallback):
    def __init__(self):
        RecognizeCallback.__init__(self)

    def on_data(self, data): # why is the transcript not showing up in on-data
        try:
            print(data["results"][0]["alternatives"][0]["transcript"])
        except Exception as e:
            print("Couldn't parse data object.", e)

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
            content_type= content_type,
            recognize_callback=callback,
            model='en-US_BroadbandModel',
            interim_results=True,
            max_alternatives=1)
    )
    stt_stream_thread.start()

    # return everything needed by main script
    return {'audio_source': audio_source,
            'stream_thread': stt_stream_thread}


# return transcribed output
# put auth in main script
# finish this