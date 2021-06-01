# Python Script For Virtual Agent


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
Only error I could not account for is if the message to 
STT Watson Services is not null but contains no words. The error does not cause the program to crash but looks like this:
    in on_data 
    `hypothesis = json_object['results'][0]['alternatives'][0][`    
