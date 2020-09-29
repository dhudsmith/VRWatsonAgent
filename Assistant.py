import json
from ibm_watson import AssistantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

#pip install --upgrade "ibm-watson>=4.7.1"
def assistant(val):
    authenticator = IAMAuthenticator('2-NzDzHD2I67WYM6MRPX7fiPCejIwZWJOvIw-Zegy212')
    assistant = AssistantV1(
        version='2020-04-01',
        authenticator=authenticator
    )

    assistant.set_service_url('https://api.us-south.assistant.watson.cloud.ibm.com/instances/a55f5e50-4d0f-46f3-9213-5e900b140660')

    response = assistant.message(
        workspace_id='c42f8322-0294-4d05-88ef-9d5f53414508',
        input={'text': val}
    ).get_result()

    return str(response["output"]["text"])
