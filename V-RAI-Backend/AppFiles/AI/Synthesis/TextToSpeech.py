from typing import Callable
from collections import deque as Queue

import requests
import re as regex
#

class Synthesizer:
    ___lastCreatedId : int = 0
    
    _sentenceQueue : Queue
    
    _haltCommand : bool = False
    _safeToStop : bool = False
    
    _onPartialOutputCallbackFunction : Callable[[bytes], None]

    _aiSeverURL : str = "localhost:5003/synthesizeText"
    
    def __init__(self,  name : str = "", ) -> None:
        ##init p1    
        if not name:
            name = "AISpeechSynthesizer." + str(Synthesizer.___lastCreatedId)
            Synthesizer.___lastCreatedId += 1            
        self.name = name
        print("\nInitializing AISpeechSynthesizer, name set as: " + self.name)

        ##init p2
        self._sentenceQueue = Queue()

        # TODOIMP!!!: test AI model to cache

        ##init end
        print(self.providePropertiesInfo())                   

    def providePropertiesInfo(self) -> str:
        return str(
            "Properties set for " + str(self.name) + " are:\n"
            +"Synthesizer AI model ==>  module -> speechbrain.pretrained | class -> Tacotron2 -> device = ???(Please check AI terminal for this info.)\n"
            +"Vocoder AI model ==>  module -> speechbrain.pretrained | class -> HIFIGAN -> device = ???(Please check AI terminal for this info.)"
            )
    
    def SetPartialOutputReceivingFunction(self, functionToCall : Callable[[bytes], None]) -> None:
        self._onPartialOutputCallbackFunction = functionToCall
    
    def GetCompleteInput(self, sentence : str) -> None:
        if(self._haltCommand == True):  
            return                  
        
        self._sentenceQueue.append(sentence)
        self._synthesizeSentenceQueue()
     
    def _synthesizeSentenceQueue(self) -> None:                    
        item_count = len(self._sentenceQueue)
        for i in range(item_count):   
            if(self._haltCommand == True):    
                return     
            text : str = self._sentenceQueue.popleft()
            print(text)
            alphabet_search = regex.search('[A-Za-z]', text)
            if alphabet_search is not None:    
                self.SynthesizeTextToOGGAudio_b64(text)      
        
    def SynthesizeTextToOGGAudio_b64(self, inputText : str) -> None:             
        if(self._haltCommand  == True):
            return ""              
    
        isMatch = regex.match(pattern='#[a-zA-Z0-9]+#',string=text_input)
        if(isMatch):
            text_input = text_input.replace(isMatch[0], "")
        
        print(self.name + " is synthesizing text to speech.")    
                
        inputObj = {
            "textToSynthesize" : text_input
        }        
        
        response = requests.post(self._aiSeverURL, json=inputObj) 
        outputObj = response.json()
        
        ogg_b64Value = outputObj["ogg_b64"]       
        
        if(ogg_b64Value == ""):
            print("Nothing was synthesized.")
            return
        
        if(self._onPartialOutputCallbackFunction is not None):
            self._onPartialOutputCallbackFunction(ogg_b64Value)            
            
    def ReinitializeProcessing_CrossThreadCommand(self) -> None:
        self._haltCommand = False   
        self._sentenceQueue = Queue()        
            
    def HaltProcessing_CrossThreadCommand(self) -> None:
        self._haltCommand = True   
pass

##TODO: Confirm each sentence is being printed