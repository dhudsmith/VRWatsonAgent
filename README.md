# Python Script For Virtual Agent

This directory creates a server, and needs a client (such as the Unity Demo) to fully operate


# Setup:
to run this file the following environmental variables need to be set:
- ASSISTANT_APIKEY
- ASSISTANT_ID
- STT_APIKEY
- DALLAS_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com/;
- TTS_APIKEY
- TTS_SERVICEURL (do not include "http://" as a websocket connection is used) 

All of these variables can be found on an instance of the corresponding service on IBM Watson's website

# Flow:
The following image walks through the general flow of information within the program

![image](https://user-images.githubusercontent.com/79411863/120489807-eb427580-c385-11eb-90af-b6ca5dac0a0d.png)

Currently, the python script (main app) waits for all audio and concatenates it before sending back to the Unity Demo, however it is possible to stream the audio from the python app


# Files:
`app.py`:
responsible for creating and maintaining server,
runs the main logic of program, such as:
- receiving messages
- invoking proper watson services
- sending messages

`watsonUtilities.py`:
Handles all functioncality for watson STT, Assistant and TTS
Contains classes:
- WatsonTTS - text to speech and related functions
- WatsonSTT - speech to text and related functions
- Assistant - interpreting messages for answers

`transcript.py`
    contains a record of the current trancript 

`SocketMessage.py`
    contains a way to encapsulate data to send over web socket

# Known issues:
Only error I could not account for is if the message to STT Watson Services is not null but contains no words (such as just background noise or white noise).
The error does not cause the program to crash but looks like this:

   in on_data 
    `hypothesis = json_object['results'][0]['alternatives'][0][`    
