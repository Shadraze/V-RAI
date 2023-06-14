using System;
using System.IO;
using System.Diagnostics;

using Debug = UnityEngine.Debug;

using UnityEngine;
using UnityEngine.Networking;

using CustomAudioHelpers;

using GroovyCodecs.Mp3;
using GroovyCodecs.WavFile;
using GroovyCodecs.Types;
using System.Collections;
using System.Collections.Generic;
using System.Timers;

public class Recorder : MonoBehaviour
{
    class SendObj
    {
        public string commandType = "";
        public string userInputAudio_mp3 = "";
    }

    class ReceiveObj
    {
        public string executeAFunction = "";
        public string aiResponseAudio_ogg = "";
    }

    private bool haltCommand = false;

    private AudioClip buffer;
    private static IMp3Encoder _lameEnc;
    private Stopwatch timer;

    public ServerAIConnection server;   
    private readonly Queue<AudioClip> receivedAudioQ = new();    
    private static bool audioPlaying = false;
    public AudioSource audioSource;

    public void StartRecording()
    {
        foreach(string device in Microphone.devices)
        {
            print(device);
        }

        this.buffer = Microphone.Start(Microphone.devices[0], false, 70, 44100);        

        if(this.buffer == null)
        {
            Debug.LogWarning("Source: Recorder class -> StartRecording(). Issue: Failed to start recording with Microphone.start().");
            return;
        }   

        timer = new Stopwatch();
        timer.Start(); 
    }

    public void StopRecording()
    {
        if(this.buffer == null) return;

        Microphone.End(Microphone.devices[0]);
        
        byte[] processedDataBytes_MP3;
        int processedDataLength;
        (processedDataBytes_MP3, processedDataLength) = this.ProcessRecordedBufferToMP3();  

        haltCommand = false;   
        SendToServer(processedDataBytes_MP3,processedDataLength);

        // FileStream outputFile = File.Create(Application.dataPath + "/recorded.mp3", processedDataLength);
        // outputFile.Write(processedDataBytes_MP3, 0, processedDataLength);
        // outputFile.Close();

        timer.Stop();  
    }

    public void Halt()
    {
        SendObj sendObj = new();
        sendObj.commandType = "halt";

        string sendString = JsonUtility.ToJson(sendObj);

        ServerAIConnection.ClearOutQ();

        haltCommand = true;       
        ServerAIConnection.SendNewMessage(sendString);
    }

    private (byte[],int) ProcessRecordedBufferToMP3()
    {
        uint audioLength = 0;
        byte[] wavBytes = SavWav.GetWav(this.buffer, out audioLength, true);      

        Debug.Log("Recorder class. Recorded wav bytes size: " + audioLength.ToString());
        
        _lameEnc = new Mp3Encoder();

        WavReader audioFile = new WavReader();        
        audioFile.OpenFile(wavBytes);

        AudioFormat srcFormat = audioFile.GetFormat();
        _lameEnc.SetFormat(srcFormat, srcFormat);   //weirdly written function from external sources, but it works
        
        byte[] inBuffer = audioFile.readWav();
        byte[] outBuffer = new byte[inBuffer.Length];
        int mp3Length = _lameEnc.EncodeBuffer(inBuffer, 0, inBuffer.Length, outBuffer);
        
        _lameEnc.Close();
        
        Debug.Log("Recorder class. Recorded mp3 bytes size: " + mp3Length.ToString());

        return (outBuffer, mp3Length);
    }


    private void SendToServer(byte[] fileBytes, int length)
    {
        string mp3Base64 = Convert.ToBase64String(fileBytes,0,length);

        SendObj sendObj = new();
        sendObj.userInputAudio_mp3 = mp3Base64;


        string sendString = JsonUtility.ToJson(sendObj);

        ServerAIConnection.SendNewMessage(sendString);
    }
    
    string last_message = "";        
    private void Update()
    {
        if((last_message = ServerAIConnection.ProvideLastReceivedMessage()) != "")
        {
            ReceiveFromServer(last_message);
        }
    }

    Queue<string> receivedMessages = new();
    private void ReceiveFromServer(string receivedString) 
    {
        //Only Audio part for now
        //distribute data where appropriate in this function, later
        if(receivedString != "")
        {
            ReceiveObj receivedObj = JsonUtility.FromJson<ReceiveObj>(receivedString);

            if(receivedObj.aiResponseAudio_ogg != "")
            {
                byte[] oggBase64 = Convert.FromBase64String(receivedObj.aiResponseAudio_ogg);

                AudioClip audioClip = createAudioClip(oggBase64);  
                receivedAudioQ.Enqueue(audioClip);             

                if(!audioPlaying)
                {StartCoroutine(PlayResponseAudioQ()); }
            }
            else if(receivedObj.executeAFunction != "")
            {
                ExecuteFunction(receivedObj.executeAFunction);
            }
        }
    }

    public GameObject position;
    public GameObject cube;
    public GameObject spaceship;

    private void ExecuteFunction(string functionName)
    {
        switch(functionName)
        {
            case "#putacube#":
                Put(cube);
                break;
            case "#put10cube#":
                for(int i = 0; i<10; i++)
                {
                    Put(cube);
                }
                break;
            case "#putspaceship#":
                Put(spaceship);
                break;
            default:
                break;
        }
    }

    private void Put(GameObject resource)
    {
        GameObject gobj = GameObject.Instantiate(resource);
        gobj.transform.position = position.transform.position;
    }

    private AudioClip createAudioClip(byte[] oggBase64)
    {
        UnityWebRequest localFile = new();

        File.WriteAllBytes(Application.dataPath + "/received.ogg", oggBase64);

        using (UnityWebRequest wwwlocal = UnityWebRequestMultimedia.GetAudioClip("file://" + Application.dataPath + "/received.ogg", AudioType.OGGVORBIS))
        {
            var result = wwwlocal.SendWebRequest();

            while (!result.isDone) {}

            if (wwwlocal.result == UnityWebRequest.Result.ConnectionError)
            {
                Debug.Log(wwwlocal.error);
            }
            else
            {
                return DownloadHandlerAudioClip.GetContent(wwwlocal);
            }
        }        

        return null;
    }

    float lastClipTime = 0; 
    Stopwatch clipStopWatch = new();    
    IEnumerator PlayResponseAudioQ()
    {
        if(haltCommand == true)
        {
            yield break;
        }

        audioPlaying = true;
        while(receivedAudioQ.Count != 0)
        {
            audioSource.clip = receivedAudioQ.Dequeue();

            lastClipTime = audioSource.clip.length*1000;

            audioSource.Play(22050);

            while(audioSource.isPlaying)
            {
                if(haltCommand == true)
                {
                    audioSource.Stop();
                    audioPlaying = false;
                    receivedAudioQ.Clear();
                    yield break;
                }

                yield return null;
            }
        }
        audioPlaying = false;

        yield break;
    }
}

