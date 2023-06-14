from typing import Callable

import re as regex
from collections import deque as Queue
#

class TokensToSentence:    
    ___lastCreatedId : int = 0
    
    _sentenceQueue : Queue
    _tokenQueue : str = ""
    
    _haltCommand : bool = False
    _safeToStop : bool = False

    #some regex to split input text into smaller chunks for synthesis     
    alphabets= "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov|edu|me)"
    digits = "([0-9])"
    
    _onPartialOutputCallbackFunctions : list[Callable[[str], None]]
    
    def __init__(self,  name : str = "", ) -> None:
        self._sentenceQueue = Queue()
        self._tokenQueue = ""
        self._onPartialOutputCallbackFunctions = list[Callable[[str], None]]()
        
    def AppendPartialOutputReceivingFunction(self, functionToCall : Callable[[str], None]) -> None:
        self._onPartialOutputCallbackFunctions.append(functionToCall)
     
    def GetPartialInput(self, token : str) -> None:
        if(self._haltCommand == True):    
            return          
        
        #print(token, end="", flush= True)
        self._tokenQueue += token      

        sentenceArray = self.split_into_sentences(self._tokenQueue)
        if(len(sentenceArray) > 1): 
            self._sentenceQueue.append(sentenceArray[0])
            self._tokenQueue = sentenceArray[1]
            self._outputSentenceQueue()
            
    def split_into_sentences(self, text) -> None:        
        text = " " + text + "  "    
        text = text.replace("\n",".")   #
        text = regex.sub(self.prefixes,"\\1<prd>",text)
        text = regex.sub(self.websites,"<prd>\\1",text)
        text = regex.sub(self.digits + "[.]" + self.digits,"\\1<prd>\\2",text)
        if "..." in text: text = text.replace("...","<prd><prd><prd>")
        if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
        text = regex.sub("\s" + self.alphabets + "[.] "," \\1<prd> ",text)
        text = regex.sub(self.acronyms+" "+self.starters,"\\1<stop> \\2",text)
        text = regex.sub(self.alphabets + "[.]" + self.alphabets + "[.]" + self.alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
        text = regex.sub(self.alphabets + "[.]" + self.alphabets + "[.]","\\1<prd>\\2<prd>",text)
        text = regex.sub(" "+self.suffixes+"[.] "+self.starters," \\1<stop> \\2",text)
        text = regex.sub(" "+self.suffixes+"[.]"," \\1<prd>",text)
        text = regex.sub(" " + self.alphabets + "[.]"," \\1<prd>",text)
        if "”" in text: text = text.replace(".”","”.")
        if "\"" in text: text = text.replace(".\"","\".")
        if "!" in text: text = text.replace("!\"","\"!")
        if "?" in text: text = text.replace("?\"","\"?")
        text = text.replace(".",".<stop>")
        text = text.replace("?","?<stop>")
        text = text.replace("!","!<stop>")    
        text = text.replace("<prd>",".")
        sentences = text.split("<stop>")
        #sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]
        return sentences
               
    def _outputSentenceQueue(self) -> None:                    
        item_count = len(self._sentenceQueue)
        for i in range(item_count):        
            if(self._haltCommand == True):       
                return
            text : str = self._sentenceQueue.popleft()
            print(text)
            alphabet_search = regex.search('[A-Za-z]', text)
            command_search = regex.search('#[A-Za-z0-9]+#',text)
            if (alphabet_search is not None 
            and self._onPartialOutputCallbackFunctions is not None):  
                for i in range(len(self._onPartialOutputCallbackFunctions)):
                    self._onPartialOutputCallbackFunctions[i](text) # this can take time depending on what the outputs do
                       
    def ReinitializeProcessing_CrossThreadCommand(self) -> None:
        self._haltCommand = False     
        #input queue clear   
        self._tokenQueue = ""
        self._sentenceQueue = Queue()
            
    def HaltProcessing_CrossThreadCommand(self) -> None:
        self._haltCommand = True                 

##TODO: Confirm each sentence is being printed