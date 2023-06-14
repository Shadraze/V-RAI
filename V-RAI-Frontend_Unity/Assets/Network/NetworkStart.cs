using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Netcode;
using Unity.Netcode.Transports.UTP;
using System.Net;

using Debug = UnityEngine.Debug;
using System;

public class NetworkStart : MonoBehaviour
{
    public bool runStart = false;

    private void Start()
    {
        if(!runStart) return;

        string serverAddress = this.gameObject.GetComponent<UnityTransport>().ConnectionData.Address;

        if(CheckIfIsServer(serverAddress))
        {
            Debug.LogWarning("Starting Server.");
            StartAsServer();
        }
        else
        {
            StartAsClient();
        }
    }

    public bool CheckIfIsServer(string url)
    {
        IPHostEntry iphostentry = Dns.GetHostEntry (Dns.GetHostName ());
        IPHostEntry other = null;
        try {
            other = Dns.GetHostEntry (url);
        } catch {
            Debug.LogWarning("Unknown host: " + url);
        }
        foreach (IPAddress addr in other.AddressList) {
            if (IPAddress.IsLoopback (addr) || Array.IndexOf (iphostentry.AddressList, addr) != -1) {
                Debug.Log (url + " IsLocal");
                return true;
            } 
        }
    
        return false;
    }

    public void StartAsServer()
    {
        this.gameObject.GetComponent<NetworkManager>().StartServer();
    }

    public void StartAsClient()
    {
        this.gameObject.GetComponent<NetworkManager>().StartClient();
    }
}


// IPAddress[] host;
// IPAddress[] local;
// bool isLocal = false;

// host = Dns.GetHostAddresses(url);
// local = Dns.GetHostAddresses(Dns.GetHostName());

// foreach (IPAddress hostAddress in host)
// {
//     if (IPAddress.IsLoopback(hostAddress))
//     {
//         isLocal = true;
//         break;
//     }
//     else
//     {
//         foreach (IPAddress localAddress in local)
//         {
//             if (hostAddress.Equals(localAddress))
//             {
//                 isLocal = true;
//                 break;
//             }
//         }

//         if (isLocal)
//         {
//             break;
//         }
//     }
// }

// if(isLocal) return true;
// else return false;