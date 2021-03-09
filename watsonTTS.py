from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os

if __name__ =='__main__':
    # setup stt
    tts_apikey = os.getenv('TTS_APIKEY')
    dallasUrl = os.getenv('TTS_SERVICEURL')

    authenticator = IAMAuthenticator(tts_apikey)
    text_to_speech = TextToSpeechV1(
        authenticator=authenticator
    )
    text_to_speech.set_service_url(dallasUrl)

    with open('test.wav', 'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(
                'Let me not to the marraige of true minds admit impediment. Love is not love which alters when it alteration finds, or bends with the remover to remove. On no it is an ever fixed mark',
                voice='en-US_KevinV3Voice',
                accept='audio/wav'
            ).get_result().content)


