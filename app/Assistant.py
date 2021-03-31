from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class Assistant:
    def __init__(self, apikey, assistant_id):


        self.apikey = apikey
        self.assistant_id = assistant_id

        # authenticate
        authenticator = IAMAuthenticator(apikey)
        self.assistant = AssistantV2(
            version='2020-04-01',
            authenticator=authenticator,
        )

        # create a session
        response = self.assistant.create_session(
            assistant_id=self.assistant_id
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
            assistant_id=self.assistant_id,
            session_id=self.session_id,
            input=input,
            context=context
        ).get_result()

        try:
            return str(response["output"]['generic'][0]['text'])
        except Exception:
            return "<NO RESPONSE>"

if __name__=='__main__':
    import os
    apikey = os.getenv('ASSISTANT_APIKEY')
    assistant_id = os.getenv('ASSISTANT_ID')
    assistant = Assistant(apikey, assistant_id)

    print(assistant.message("Hi bob, how are you?", "TS4"))

