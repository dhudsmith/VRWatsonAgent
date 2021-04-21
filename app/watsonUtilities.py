from ibm_watson import SpeechToTextV1
from ibm_watson import TextToSpeechV1
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from threading import Thread
from ibm_watson.websocket import RecognizeCallback, AudioSource
from transcript import Transcript
from queue import Queue
import sys
import traceback
import os

# setup tts
tts_apikey = os.getenv('TTS_APIKEY')
serviceURL = os.getenv('TTS_SERVICEURL')

# setup stt
stt_apikey = os.getenv('STT_APIKEY')
dallasUrl = os.getenv('DALLAS_URL')

assistant_apikey = os.getenv('ASSISTANT_APIKEY')
assistant_URL = os.getenv('ASSISTANT_ID')


class watsonTTS:
    def __init__(self):
        self.authenticator = IAMAuthenticator(tts_apikey)
        self.text_to_speech = TextToSpeechV1(
            authenticator=self.authenticator
        )
        self.text_to_speech.set_service_url(serviceURL)

    def callSpeech(self, transcript: Transcript):
        if transcript.assistantResponse != "<NO RESPONSE>":
            with open('Response.wav', 'wb') as audio_file:
                audio_file.write(
                    self.text_to_speech.synthesize(
                        transcript.assistantResponse,
                        voice='en-US_KevinV3Voice',
                        accept='audio/wav' #l16
                    ).get_result().content)


# transcript buffer
BUFFER_MAX_ELEMENT = 20
transcript_queue = Queue(maxsize=BUFFER_MAX_ELEMENT)


class watsonSTT:
    def __init__(self, buffer_queue: Queue, content_type: str, transcript: Transcript):
        """
        Type some stuff about the class
        :param buffer_queue: describe what this does
        :param content_type:
        :param transcript:
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
            RecognizeCallback.__init__(self)
            self.callTranscript = transcript

        def on_data(self, data):  # why is the transcript not showing up in on-data
            try:
                results = data['results'][0]
                transcript = results['alternatives'][0]['transcript']
                if results["final"]:
                    self.callTranscript.originalMessage = transcript
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
        
        :param buffer_queue:
        :param content_type:
        :return:
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
        self.stream["audio_source"].completed_recording()
        self.stream["stream_thread"].join()

    def pop_transcript_queue(self):
        transcript = []
        while transcript_queue.qsize() > 0:
            transcript.append(transcript_queue.get())
        return transcript


class Assistant:
    def __init__(self):

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