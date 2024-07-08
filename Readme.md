# V-RAI

V-RAI is my 7th semester internship project. The project takes input from a VR headset's microphone, synthesizes it with OpenAI Whisper, 
generates text based on user input using GPT3.5 through the OpenAI API, and finally vocodes it using Tactotron2.
This constitutes the backend of the project.

The frontend of the project is in Unity, more specifically you want to use Unity 2022 to compatibility. The Meta Quest 2 is also a requirement
as the project was made with that headset in mind.

The backend of the project can still run without a frontend through POST requests on the Flask API.

Note:
The OpenAI API key in V-RAI-Backend/AppFiles/AI/Generation/TextToText.py is invalid. In order for the project to work, an OpenAI API key is needed! 
OpenAI provides free trial of their API to new accounts, you may use that for testing purposes. Or may replace the model with a local LLM.
