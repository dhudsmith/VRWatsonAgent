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
        content_type='audio/l16;rate=22050;channels=1',
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

# return transcribed output
# put auth in main script
# finish this