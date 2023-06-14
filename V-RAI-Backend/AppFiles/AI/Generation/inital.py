from collections import deque

systemMessage = ""
chatMessages = list

def fillInitial():
    systemMessage = 'Always respond in this format:\n\n'

    +'{\n'
    +'"userWantsMeTo" : "X"\n'
    +'\n}'
    +'Y\n\n\n'


    +'(Note : replace X with one of options- putCube, put10Cube, putSpaceship, autopilotSpaceship, converseOrAudioRelated, unimplemented. )\n\n'

    +'(Note : don\'t ever make up an option)\n\n'

    +'(Note: You are connected to a text-to-speech synthesizer, so you are capable of doing audio related tasks.)\n\n'

    +'(Note : accept and try to do all audio related tasks)\n\n'

    +'(Note : replace Y with your response to user\'s message.)\n\n'

    +'(Note: only respond with "Roger." when X is neither of converseOrAudioRelated  or unimplemented)\n'
    +''

    chatMessages.append("user : put a sphere")
    chatMessages.append('assistant : {\n'
        +'"userWantsMeTo" : "unimplemented"\n'
        +'}\n'
        +'That is an unimplemented action in my instructions.')
    

    chatMessages.append("user : put my spaceship on autopilot")
    chatMessages.append('assistant : {\n'
        +'"userWantsMeTo" : "autopilotSpaceship"\n'
        +'}\n'
        +'Roger.')
    
    chatMessages.append("user : put a cube")
    chatMessages.append('assistant : {\n'
        +'"userWantsMeTo" : "putCube"\n'
        +'}\n'
        +'Roger. I have placed a cube.')