from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os

# setup tts
tts_apikey = os.getenv('TTS_APIKEY')
serviceURL = os.getenv('TTS_SERVICEURL')

class watsonTTS:
    def __init__(self, transcript):
        self.message = transcript

    def callSpeech(self):
        with open('InFunction.wav', 'wb') as audio_file:
            audio_file.write(
                text_to_speech.synthesize(
                    self.message,
                    voice='en-US_KevinV3Voice',
                    accept='audio/wav'
                ).get_result().content)



if __name__ == '__main__':
    # setup tts
    tts_apikey = os.getenv('TTS_APIKEY')
    serviceURL = os.getenv('TTS_SERVICEURL')

    authenticator = IAMAuthenticator(tts_apikey)
    text_to_speech = TextToSpeechV1(
        authenticator=authenticator
    )
    text_to_speech.set_service_url(serviceURL)

    with open('main.wav', 'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(
                'Testing, 1, 2, 3.',
                voice='en-US_KevinV3Voice',
                accept='audio/wav'
            ).get_result().content)
