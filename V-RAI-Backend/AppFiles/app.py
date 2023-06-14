from collections import deque

import re as regex

import asyncio
import websockets
import json
import base64

from websockets.server import WebSocketServerProtocol
from concurrent.futures import ThreadPoolExecutor

from AI.Transcription.SpeechToText import Transcriber as AITextTranscriber
from AI.Generation.TextToText import Generator as AITextGenerator
from AI.Synthesis.TextToSpeech import Synthesizer as AISpeechSynthesizer
from Utils.TokensToSentence import TokensToSentence as UtilTokenToSentence
#

class ThreadedSpeechToSpeechAIChain:    
    _t : AITextTranscriber
    _g : AITextGenerator
    _u : UtilTokenToSentence
    _s : AISpeechSynthesizer
    
    _threadExecutor : ThreadPoolExecutor
    _sendExecutor : ThreadPoolExecutor
    _threadExecutorRunning : bool = False
    _haltThreadCommand : bool = False
    _sendExecutorRunning : bool = False
    
    #input related
    _nextInputId : int = 0 
    
    _inputQ : deque[dict]
    _outputQ : deque[str]
            
    #output related
    _outputSink : str = ""
    _websocket : WebSocketServerProtocol
            
    def __init__(self) -> None:                        
        self._t = AITextTranscriber()
        self._g = AITextGenerator()
        self._u = UtilTokenToSentence()
        self._s = AISpeechSynthesizer()     
        
        self._threadExecutor = ThreadPoolExecutor(1)
        self._sendExecutor = ThreadPoolExecutor(1)
        
        self._inputQ = deque[dict]()
        self._outputQ = deque[str]()
        
        #creating the AI processing chain
        self._t.SetCompleteOutputReceivingFunction(self._g.GetCompleteInput)
        self._g.SetPartialOutputReceivingFunction(self._u.GetPartialInput)
        
        self._u.AppendPartialOutputReceivingFunction(self._OutputLogic_B)
        
        self._u.AppendPartialOutputReceivingFunction(self._s.GetCompleteInput)
        self._s.SetPartialOutputReceivingFunction(self._OutputLogic_A)   
        
        #cache run?, next becomes faster
        #
    
    def SetCurrentWebSocket(self, currentWebsocket : WebSocketServerProtocol) -> None:
        self._websocket = currentWebsocket        
        
    def ConsultChainForOutput(self, inputFilePath : str) -> str:
        self._outputComplete=False
        self._t.GetCompleteInput(inputFilePath)
        return self._lastOutputFilePath    
    
    def InputLogic(self, inputJSONMsg : str):       
        inputObj : dict = json.loads(inputJSONMsg)          
        self._nextInputId += 1
        #        
                
        if(inputObj["commandType"] == "halt"):
            self._RunHaltLogic()
        else:
            self._inputQ.append(inputObj)      
            self._RunAIConsultLogic()        
    
    def _RunHaltLogic(self):
        #check if executor thread is running
        #if no, return
        if not self._threadExecutorRunning:
            return        
        
        #, else perform safety checks and halt the thread
        #change the var that determines check for final output sink of ai chains so that no futher responses are sent
        self._outputSink = "halt"
        
        #perform safety checks and clear input queues where needed  
        self._haltThreadCommand = True         
        self._t.HaltProcessing_CrossThreadCommand()
        self._u.HaltProcessing_CrossThreadCommand()
        self._s.HaltProcessing_CrossThreadCommand()
        #now transcriber and synthesizer are free
                 
        #stop the executor thread
        self._threadExecutor.shutdown()
        self._threadExecutorRunning = False
                
        #clean input queues of this class
        self._inputQ.clear()
    
    def _RunAIConsultLogic(self):        
        #check if thread is running already
        #if no leave it be        
        if self._threadExecutorRunning:
            return
                    
        #, else initialize and start a thread, to run ai consult logic in the background
        #set check for final output sink of ai chains
        self._outputSink = "respond"
        
        #connect each model's inputs and output to each other/this    
        self._t.ReinitializeProcessing_CrossThreadCommand() 
        self._u.ReinitializeProcessing_CrossThreadCommand()
        self._s.ReinitializeProcessing_CrossThreadCommand()
        
        #start the thread
        self._haltThreadCommand = False    
        self._threadExecutor = ThreadPoolExecutor(1);     
        self._threadExecutor.submit(self.___AIConsult_Threaded_Logic)        
    
    def ___AIConsult_Threaded_Logic(self):        
        self._threadExecutorRunning = True
        
        while(len(self._inputQ) != 0 and self._haltThreadCommand == False):
            # note if there are long running processes in the loop, thread doesn't halt through just this
            # as it won't reach end of loop in acceptable time
            
            
            #processJSON
            inputObj : dict = self._inputQ.popleft()        
            inputAudioBytes_Mp3 : bytes = base64.b64decode(inputObj["userInputAudio_mp3"])
            
            #save the audio it contained            
            file = open("user_voice_recording.mp3","wb")
            file.write(inputAudioBytes_Mp3)
            file.close()
            
            # pass it to the beginning of the AI chain
            self._t.transcribeFile("user_voice_recording.mp3")
                        
        self._threadExecutorRunning = False
        pass      
    
    def _OutputLogic_A(self, outputAudio_b64 : str) -> None:
        if self._outputSink == "halt":
            # do nothing
            return
        else:            
            # output sink == respond, talk to socket
            
            #wrap data into json
            responseJSONobj : dict = {
                "executeAFunction" : "",
                "aiResponseAudio_ogg" : outputAudio_b64
            }            
             
            self._outputQ.append(json.dumps(responseJSONobj))  
            
            #send through socket     
            if(self._sendExecutorRunning == False):
                self._sendExecutor.submit(self.___WebSocketSend_Threaded_Logic)    
                self._sendExecutorRunning = True                        
       
    
    def _OutputLogic_B(self, generatedSentence : str) -> None:
        #this special logic block finds if the AI generator's generated text contains info on any function to execute 
        #as instructed to it through its its beginning system message (in the class itself, for now)
               
        if self._outputSink == "halt":
            # do nothing
            return
        else:            
            # output sink == respond, talk to socket
            
            #extract the function to execute
            isMatch = regex.match(pattern='#[a-zA-Z0-9]+#',string=generatedSentence)
            
            if(isMatch):
                task : str = isMatch[0]
                print(task)
                #wrap data into json
                responseJSONobj : dict = {
                    "executeAFunction" : task,
                    "aiResponseAudio_ogg" : ""
                }            
                      
                self._outputQ.append(json.dumps(responseJSONobj))  
                
                #send through socket      
                if(self._sendExecutorRunning == False): 
                    self._sendExecutor.submit(self.___WebSocketSend_Threaded_Logic)      
                    self._sendExecutorRunning = True       
                   
    
    def ___WebSocketSend_Threaded_Logic(self) -> None: 
        if(self._websocket is None): 
            self._sendExecutorRunning = False
            return 
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.wsSend())
        
        self._sendExecutorRunning = False
        print("Sent all of last input's outputs.")
    
        loop.close()
        
    async def wsSend(self) -> None:
        while(len(self._outputQ) != 0):
            if self._haltThreadCommand == True:
                self._outputQ.clear()
                break
            
            await self._websocket.send(self._outputQ.popleft())         
#

###
websocketTaskProcessor : ThreadedSpeechToSpeechAIChain = ThreadedSpeechToSpeechAIChain()

#Keyboard interupt(Ctrl+C) will stop the server, for now. if not properly stopped, close the code editor or terminal before starting again 
async def start_server():
    stopSignal : asyncio.Future = asyncio.Future() 
    async with websockets.serve(server_handler, "localhost", 7002, max_size = None):    #change max_size to limited later
        await stopSignal  # asyncio will run server unitl this asyncio.Future object's result is set,
    print("Server stopped successfully.")
    
# create handler for each connection
async def server_handler(websocket : WebSocketServerProtocol):  
    try:   
        while(True):
            stringMessage_JSON : str = await websocket.recv()          
            #TODO: need to perform checking if msg is json or not
                    
            websocketTaskProcessor.SetCurrentWebSocket(currentWebsocket=websocket)        
            websocketTaskProcessor.InputLogic(inputJSONMsg=stringMessage_JSON)            
    except websockets.ConnectionClosedOK:
        print("Exception: Connection closed abruptly!")
        pass  
  
print("Server has started.")

asyncio.run(start_server())        
####












### possibly useful code
#     outputFilePath:str = self._outputDirectory+"/"+"ai_voice_output.ogg"        
#     f = open(outputFilePath,"wb")
#     f.write(audioBytes)
#     f.close()
#     self._lastOutputFilePath = outputFilePath
#     self._outputComplete = True

# task.completed = False
# _executor.submit(task.threadableProcessing, (file_bytes))   #TODO: stop all threads when server is stopped

# while(not task.isCompleted() or task.queueHasItem()):
#     if(task.queueHasItem()):
#         await websocket.send(task.returnNextInQueue())
#     else:
#         await asyncio.sleep(0.7)      