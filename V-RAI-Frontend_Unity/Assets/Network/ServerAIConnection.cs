using UnityEngine;
using System.Threading.Tasks;
using System.Threading;
using System.Net.WebSockets;
using System;
using System.Collections.Generic;
using System.Text;

public class ServerAIConnection : MonoBehaviour
{
    private class CustomMessageBuffer
    {
        public readonly Queue<string> sendQ = new();
        public readonly Queue<string> receiveQ = new();        
        public readonly List<ArraySegment<byte>> currentReceive = new();
    }

    private static readonly string url = "ws://localhost:7002";
    private static ClientWebSocket connection;
    private static CustomMessageBuffer messageBuffer = new();

    private static Task connectionThread;
    private static Task receiveThread;
    private static readonly CancellationTokenSource connectionThreadControl = new();
    private static bool unityServerRunning = true;
    private static int connectionThreadLogicPhase = 0;


    // Start is called before the first frame update
    private void Start()
    {
        BeginAIConnectionThread();        
    }

    private void BeginAIConnectionThread()
    {
        connectionThread = Task.Run(AIConnection, connectionThreadControl.Token);
    }

    private static async void AIConnection()
    {
        while(unityServerRunning)
        {
            switch (connectionThreadLogicPhase)
            {
                case 0:
                    await TryToConnectToServer();      
                    break;            
                case 1:
                    receiveThread = Task.Run(ReceiveTask,connectionThreadControl.Token);
                    connectionThreadLogicPhase++;   
                    break;
                case 2:
                    RunConnectionQueueLogic();
                    break;
                default:
                    Debug.LogError("AIConnection() switch case code is in default block! This should not have happened!");
                    break;
            }

            await Task.Delay(347,connectionThreadControl.Token);
        }
    }

    private static async Task TryToConnectToServer()
    {
        try
        {
            connection = new();
            await connection.ConnectAsync(new Uri(url),connectionThreadControl.Token);
            connectionThreadLogicPhase++;   
            Debug.Log("Connection to AI server has succeded.");            
        }
        catch(Exception e)
        {
            Debug.LogError("Couldn't connect to AI server, with exception:\n"
            + e.Message + "\n" + e.StackTrace);
        }
    }
 
    private static async void ReceiveTask()
    {
        try
        {
            while(unityServerRunning)
            { 
                messageBuffer.currentReceive.Add(
                    new ArraySegment<byte>(new byte[1024*1024*7]));   //7MB for now at once, later, try decreasing this to see if further logic even works

                WebSocketReceiveResult result = await connection.ReceiveAsync(
                    messageBuffer.currentReceive[^1]
                    ,connectionThreadControl.Token);

                int lastBytesCount = result.Count;

                string receivedMessage = "";

                //following is an example of receiving large files, for the future
                //if(result.EndOfMessage == false) continue;
                // for(int i=0; i<messageBuffer.currentReceive.Count-1;i++)
                // {
                //     receivedMessage += Encoding.UTF8.GetString(messageBuffer.currentReceive[i]);
                // }

                byte[] lastBytes = (messageBuffer.currentReceive[^1].Slice(0,lastBytesCount)).ToArray();
                receivedMessage += Encoding.UTF8.GetString(lastBytes);

                Debug.Log("Received a Message.");

                messageBuffer.receiveQ.Enqueue(receivedMessage);   
                messageBuffer.currentReceive.Clear();
            }
        }   
        catch(Exception e)
        {
            Debug.LogError("Error in receiving data, with exception:\n"
            + e.Message + "\n" + e.StackTrace);
        }
    }

    private static async void RunConnectionQueueLogic()
    {
        try
        {
            //sending logic
            while(messageBuffer.sendQ.Count != 0)
            {
                string Message = messageBuffer.sendQ.Dequeue();
                await connection.SendAsync(
                    new ArraySegment<byte>(Encoding.UTF8.GetBytes(Message))
                    ,WebSocketMessageType.Text
                    ,true
                    ,connectionThreadControl.Token);
            }                
        }
        catch(Exception e)
        {
            Debug.LogError("Error in sending or receiving data, with exception:\n"
            + e.Message + "\n" + e.StackTrace);
        }
    }

    private void OnDestroy()
    {
        Debug.LogWarning("The AI Server Unity Program is closing down.");

        connectionThreadControl.Cancel(true);
        unityServerRunning = false;
        connection.CloseAsync(WebSocketCloseStatus.EndpointUnavailable
            ,"Unity AI Server program is shutting down as instructed to."
            ,CancellationToken.None);
        connection.Dispose();

        connectionThread.Dispose();
        receiveThread.Dispose();

        Debug.LogWarning("The AI Server Unity Program is closing down normally. If this was unexpected, perform error checks.");
    }

    public static void ClearOutQ()
    {
        messageBuffer.receiveQ.Clear();
    }

    public static void SendNewMessage(string Message)
    {
        messageBuffer.sendQ.Enqueue(Message);      
    }

    public static string ProvideLastReceivedMessage()
    {
        if(messageBuffer.receiveQ.Count != 0)
        {
            return messageBuffer.receiveQ.Dequeue();
        }   
        return "";     
    }
}
