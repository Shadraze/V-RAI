from typing import Callable

import requests
#

class Transcriber:
    ___lastCreatedId : int = 0

    _onOutputCompleteCallbackFunction : Callable[[str], None]
    _name : str

    _haltCommand : bool = False
    _safeToStop : bool = False
    
    _aiSeverURL : str = "localhost:5002/transcribeAudio"

    def __init__(self, name : str = "") -> None:           
        ##init p1    
        if not name:
            name = "AITextTranscriber." + str(Transcriber.___lastCreatedId)
            Transcriber.___lastCreatedId += 1            
        self._name = name
        print("\nInitializing AITextTranscriber, name set as: " + self._name)

        ##init p2
        
        # TODOIMP!!!: test AI model to cache

        ##init end
        print(self.providePropertiesInfo())

    def providePropertiesInfo(self) -> str:
        return str(
            "Properties set for " + str(self._name) + " are:\n"
            +"Text transcription AI model ==> module -> whisper | class -> Whisper | device = ???(Please check AI terminal for this info.)"               
            )
    
    def transcribeFile(self, mp3_b64Value : str) -> None:
        if(self._haltCommand == True):    
            return
              
        self._safeToStop = False
                        
        print(self._name + " is transcribing user audio to text.")
        
        inputObj = {
            "mp3_b64" : mp3_b64Value
        }        
        response = requests.post(self._aiSeverURL, json=inputObj) 
        outputObj = response.json()
        
        result_text = outputObj["transcribedText"] if (isinstance(outputObj["text"], str)) else ""        
        
        if(result_text==""):
            result_text = "Couldn't transcribe any text. It might be an issue with the model or more likely empty output/input or improper request/response."
            print(result_text)           

        print(self._name + " transcribed audio as text successfully as:") 
        print(result_text)           

        if(self._onOutputCompleteCallbackFunction is not None):   
            self._onOutputCompleteCallbackFunction(result_text)
                        
    def GetCompleteInput(self, audioFilePath : str) -> None:
        self.transcribeFile(mp3_b64Value=audioFilePath)
    
    def SetCompleteOutputReceivingFunction(self, functionToCall : Callable[[str], None]) -> None:
        self._onOutputCompleteCallbackFunction = functionToCall
                
    def ReinitializeProcessing_CrossThreadCommand(self) -> None:
        self._haltCommand = False
            
    def HaltProcessing_CrossThreadCommand(self) -> None:
        self._haltCommand = True             
        
        
        
        