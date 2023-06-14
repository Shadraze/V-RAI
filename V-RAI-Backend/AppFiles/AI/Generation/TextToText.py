from typing import Any, Dict, List, Union, Callable

import os

from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import  CallbackManager
from langchain.schema import (AgentAction, AgentFinish, LLMResult
                              , BaseMessage, AIMessage, HumanMessage, SystemMessage)
#

class Generator(BaseCallbackHandler):    
    os.environ["OPENAI_API_KEY"] = "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"
    
    #static private vars
    ___lastCreatedId : int = 0    
    ___chatAISystemText = str(
        "You are a virtual assistant in a VR world. Try to sound natural and unrobotic.\n\n"
        +"When you receive input from the user, you can respond in two ways:\n"
        +"a)Converse\n"
        +"b)Converse + Do one action from {putacube,put10cube,putspaceship}\n\n"
        +"You need to determine if the user input is 'a' or 'b'\n\n"
        +"If its 'a', you converse as you would.\n"
        +"If its 'b' you attach the action at the start of the message in between two '#' symbols (like #putacube#).  Do NOT ask for extra info related to the activity (such as 'where to put?'), just say 'okay' instead for example.\n")


    #private
    __chatAi : ChatOpenAI 
    __chatMessages = list[BaseMessage]()
    __onPartialOutputCallbackFunction : Callable[[str], None]

    #public
    name : str

    def __init__(self,  name : str = "") -> None:
        ##init p1    
        if not name:
            name = "AITextResolver." + str(Generator.___lastCreatedId)
            Generator.___lastCreatedId += 1            
        self.name = name
        print("\nInitializing AITextResolver, name set as: " + self.name)

        ##init p2        
        self.__chatAi = self.__initializeModelAsStreaming()
        self.__chatMessages.append(SystemMessage(content=self.___chatAISystemText))
        
        ##init end
        print(self.providePropertiesInfo())
        
    def __initializeModelAsStreaming(self) -> ChatOpenAI:
        #langchain will set the client parameter so we can tell type checker to ignore the next line, NOTE!!! verbose=True was removed 
        return ChatOpenAI(streaming=True, callback_manager=CallbackManager([self]), modelName="gpt-3.5-turbo-0301" ,temperature=0.34) #type: ignore

    def providePropertiesInfo(self) -> str:
        return str(
            "Properties set for " + str(self.name) + " are:\n"
            +"Chat AI model ==>  module -> langchain.chat_models | class -> ChatOpenAI -> type = 'GPT3.5 turbo' This is a remote Chat AI model."   
        )
        
    def _ChatWithAIModel(self) -> BaseMessage:
        #this is where the chat occurs and
        #as the chat occurs, callbacks are provided by the CallbackManager
        #which are handled by the on_llm_new_token() function inherited/implemented from BaseCallbackHandler
        return self.__chatAi(self.__chatMessages)
                
    def Chat(self, withMessage : str) -> str:     
        if(withMessage == None or withMessage == "" or type(withMessage) is not str):
            return ""

        print(self.name + " is resolving text.")           
        self.__chatMessages.append(HumanMessage(content=withMessage)) 
        
        aiResponseUnformatted : BaseMessage = self._ChatWithAIModel()
                
        #NOTE!!!: Please read the _ChatWithAIModel() function and its comments as understanding it is important
        
        aiMessage : AIMessage = AIMessage(
            content=aiResponseUnformatted.content
            ,additional_kwargs=aiResponseUnformatted.additional_kwargs
            )        
        self.__chatMessages.append(aiMessage)
        
        print("\n" + self.name + " resolved text fully as:\n"+ aiMessage.content)           
        return aiMessage.content
    
    def __processNewToken(self, token: str) -> None:
        if(self.__onPartialOutputCallbackFunction is not None):
            self.__onPartialOutputCallbackFunction(token)

    def GetCompleteInput(self, newMessage : str) -> None:
        self.Chat(withMessage=newMessage)
        
    def SetPartialOutputReceivingFunction(self, functionToCall : Callable[[str], None]) -> None:
        self.__onPartialOutputCallbackFunction = functionToCall
        
    #no need for halt commands for thread safety, a process going through this class can be stopped abruptly without issue    
                
    ####section for implementation of BaseCallbackHandler, for streaming using LangChain     
    """Callback handler for streaming. Only works with LLMs that support streaming."""
    
    ##this function is implemented, for receiving/streaming of chat output strings/tokens one by one
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        self.__processNewToken(token) #move flow to one of the class functions  
    ##
        
    ## empty implementations/unused functions
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""
    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when chain errors."""
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""
    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when tool errors."""
    def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""
    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Run on agent end."""
    ##
    ####
pass


#usage#
# def example_callback(text : str) -> None:    
#     print(text, end = "", flush= True)

# if __name__ == "__main__":
#     r = Generator()
#     r.SetPartialOutputReceivingFunction(example_callback)
#     print("\n*******Type the letter 'x' to stop chatting.\n*******")
#     text : str = ""
#     while((text := input("\n : ")) != "x"):
#         r.Chat(withMessage=text)