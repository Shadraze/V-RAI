import os
import base64

from torch import cuda as Nvidia_GPU
from torch import device as Device
import whisper as SpeechToTextAI

from flask import Flask, request, jsonify

####
print("Initializing OpenAI Whisper.")
     
deviceToUse = Device("cpu")         
if(Nvidia_GPU.is_available()):
    deviceToUse = Device("cuda:0")
       
aiModel = SpeechToTextAI.load_model("base", device=deviceToUse) #SELFNOTE: again changed from in_memory=true, check if slower/faster

print("OpenAI Whisper Initialization Complete.")

#function to transcribe audio with speech to text#
def transcribeFile(mp3Bytes_b64 : str) -> str:      
    #save the audio b64 string contains            
    file = open("user_voice_recording.mp3","wb")    #extension is known for current project
    file.write(base64.b64decode(mp3Bytes_b64))
    file.close()
    
    #transcribe text
    print("OpenAI Whisper is transcribing user audio to text.")
    result_transcribedText = aiModel.transcribe(audio = "user_voice_recording.mp3")
 
    print("OpenAI Whisper transcribed audio to text successfully as:") 
    print(result_transcribedText)           
    
    #return result
    return result_transcribedText    

####           

app = Flask(__name__)
app.secret_key = os.urandom(12)

@app.route("/")
def home():    
    return "Yo. This is the AI Consultation server... of doom :O!"        
        
@app.route('/consultAI', methods=['GET','POST'])
def audioUpload():
    if request.method == 'POST':
        inputObj = request.get_json()
        
        # Check if the post request has the required field at all
        if inputObj["userInputAudio_mp3"] is None:
            print("Improper JSON format in request.")
            return "Improper JSON format in request."
        
        #processJSON    
        outputObj = {
            "transcribedText" : transcribeFile(inputObj["userInputAudio_mp3"])
        } 
        
        return jsonify(outputObj)
    
    elif request.method == 'GET':
        return 'GET block invoked, which is unsupported.' #also invoked sometimes when there is an error with POST block
    else:        
        return 'POST request required, but received neither a GET nor POST Request.'

####    