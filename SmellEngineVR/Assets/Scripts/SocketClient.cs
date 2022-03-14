// A C# program for Client 
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;

public class SocketClient : MonoBehaviour
{

    private Socket sender;
    private IPHostEntry ipHost;
    private IPAddress ipAddr;
    private IPEndPoint localEndPoint;

    // Start is called before the first frame update
    void Awake() {
        StartClient();
        //ExecuteClient(12.09);
    }

    private void OnDestroy() {
        // Close Socket using  
        // the method Close() 
        sender.Shutdown(SocketShutdown.Both);
        sender.Close();
        Debug.Log("Closing connection");
    }

    

    private void StartClient() {
        try {
            // Establish the remote endpoint  
            // for the socket. This example  
            // uses port 11111 on the local  
            // computer. 
            ipHost = Dns.GetHostEntry(Dns.GetHostName());
            ipAddr = IPAddress.Parse("127.0.0.1");//ipHost.AddressList[0];
            localEndPoint = new IPEndPoint(ipAddr, 12345);
            // Creation TCP/IP Socket using  
            // Socket Class Costructor 
            sender = new Socket(ipAddr.AddressFamily,
                       SocketType.Stream, ProtocolType.Tcp);
            // Connect Socket to the remote  
            // endpoint using method Connect() 
            sender.Connect(localEndPoint);
            // We print EndPoint information  
            // that we are connected 
            Debug.Log(string.Format("<color=green>Socket connected to -> {0}</color>",
                            sender.RemoteEndPoint.ToString()));
        } catch (Exception e) {
            Debug.Log(e.ToString());
        }
    }

    /*
     * For every element in the array, iterate over and convert to bytes,
     * once containing reference to all bytes, store to array and return.
     */ 
    static byte[] GetBytes(double[] values) {
        return values.SelectMany(value => BitConverter.GetBytes(value)).ToArray();
    }

    /*
     * For every element in the array, iterate over and convert to bytes,
     * once containing reference to all bytes, store to array and return.
     */
    static byte[] GetBytes(int[] values) {
        return values.SelectMany(value => BitConverter.GetBytes(value)).ToArray();
    }

    //void Update(){}

    public void CloseConnection() {
        try {
            // Data sent to server
            byte[] messageSent = Encoding.ASCII.GetBytes("Disconnect");
            //byte[] messageSent = BitConverter.GetBytes(sendVal);
            int byteSent = sender.Send(messageSent);
            sender.Shutdown(SocketShutdown.Both);
            sender.Close();
            Debug.Log("Closing connection");
        }
        // Manage of Socket's Exceptions 
        catch (ArgumentNullException ane) {

            Debug.Log(string.Format("ArgumentNullException : {0}", ane.ToString()));
        }
        catch (SocketException se) {

            Debug.Log(string.Format("SocketException : {0}", se.ToString()));
        }
        catch (Exception e) {
            Debug.Log(string.Format("Unexpected exception : {0}", e.ToString()));
        }
    }

    // ExecuteClient() Method 
    public void ExecuteClient(double[] transmitData) {
        try {
            //for (int i = 0; i < transmitData.Length; i++) {
            //    Debug.Log("i:\t" + i + ", D:\t" + transmitData[i]);
            //}
            // Data sent to server
            //byte[] messageSent = GetBytes(transmitData);
            //byte[] messageSent = BitConverter.GetBytes(sendVal);
            //int byteSent = sender.Send(messageSent);

            /* We receive the messagge using the method Receive(). This method returns number of bytes 
             received, that we'll use to convert them to string */
            // Data buffer 
            //byte[] messageReceived = new byte[34]; //GetBytes(new int[1]);
            //int byteRecv = sender.Receive(messageReceived);
            //Debug.Log("recv:\t" + byteRecv);
            //Debug.Log(string.Format("Message from Server -> {0}", BitConverter.ToInt32(messageReceived, 0)));
            //if (BitConverter.ToInt32(messageReceived, 0) > 0) {
            //    byte[] messageSent = GetBytes(transmitData);
            //    int byteSent = sender.Send(messageSent);
            //}
            byte[] messageSent = GetBytes(transmitData);
            int byteSent = sender.Send(messageSent);
            //Debug.Log(string.Format("Message from Server -> {0}",Encoding.ASCII.GetString(messageReceived)));
        }
        // Manage of Socket's Exceptions 
        catch (ArgumentNullException ane) {

            Debug.Log(string.Format("ArgumentNullException : {0}", ane.ToString()));
        }
        catch (SocketException se) {

            Debug.Log(string.Format("SocketException : {0}", se.ToString()));
        }
        catch (Exception e) {
            Debug.Log(string.Format("Unexpected exception : {0}", e.ToString()));
        }
    }
    

    public void ExecuteClientStop() {
        try {
            int[] transmitData = new int[1] { 1 };
            // Data sent to server
            byte[] messageSent = GetBytes(transmitData);
            //byte[] messageSent = BitConverter.GetBytes(sendVal);
            int byteSent = sender.Send(messageSent);

            /* We receive the messagge using the method Receive(). This method returns number of bytes 
             received, that we'll use to convert them to string */
            // Data buffer 

            byte[] messageReceived = new byte[4];
            int byteRecv = sender.Receive(messageReceived);
            /*Debug.Log(string.Format("Message from Server -> {0}",
                    Encoding.ASCII.GetString(messageReceived, 0, byteRecv)));*/
        }
        // Manage of Socket's Exceptions 
        catch (ArgumentNullException ane) {

            Debug.Log(string.Format("ArgumentNullException : {0}", ane.ToString()));
        } catch (SocketException se) {

            Debug.Log(string.Format("SocketException : {0}", se.ToString()));
        } catch (Exception e) {
            Debug.Log(string.Format("Unexpected exception : {0}", e.ToString()));
        }
    }

    public void TransmitPubChemIDs(List<int> transmitIDs) {
        try {
            // Data sent to server
            byte[] messageSent = GetBytes(transmitIDs.ToArray());
            int byteSent = sender.Send(messageSent);
        }
        // Manage of Socket's Exceptions 
        catch (ArgumentNullException ane) {

            Debug.Log(string.Format("ArgumentNullException : {0}", ane.ToString()));
        } catch (SocketException se) {

            Debug.Log(string.Format("SocketException : {0}", se.ToString()));
        } catch (Exception e) {
            Debug.Log(string.Format("Unexpected exception : {0}", e.ToString()));
        }
    }

    public void TransmitDilutions(int[] dilutionVals) {
        try {
            // Data sent to server
            byte[] messageSent = GetBytes(dilutionVals);
            int byteSent = sender.Send(messageSent);
        }
        // Manage of Socket's Exceptions 
        catch (ArgumentNullException ane) {

            Debug.Log(string.Format("ArgumentNullException : {0}", ane.ToString()));
        } catch (SocketException se) {

            Debug.Log(string.Format("SocketException : {0}", se.ToString()));
        } catch (Exception e) {
            Debug.Log(string.Format("Unexpected exception : {0}", e.ToString()));
        }
    }

    public void TransmitNumberOfOdorants(int[] transmitIDs) {
        try {
            Debug.Log("Transmitting #:\t" + transmitIDs[0]);
            // Data sent to server
            byte[] messageSent = GetBytes(transmitIDs);
            int byteSent = sender.Send(messageSent);
            Debug.Log("Transmitted");
        }
        // Manage of Socket's Exceptions 
        catch (ArgumentNullException ane) {

            Debug.Log(string.Format("ArgumentNullException : {0}", ane.ToString()));
        } catch (SocketException se) {

            Debug.Log(string.Format("SocketException : {0}", se.ToString()));
        } catch (Exception e) {
            Debug.Log(string.Format("Unexpected exception : {0}", e.ToString()));
        }
    }

    public void TransmitNumberOfConcentrations(int[] transmitConcs) {
        try {
            Debug.Log("Transmitting # concs:\t" + transmitConcs[0]);
            // Data sent to server
            byte[] messageSent = GetBytes(transmitConcs);
            int byteSent = sender.Send(messageSent);
            Debug.Log("Transmitted");
        }
        // Manage of Socket's Exceptions 
        catch (ArgumentNullException ane) {

            Debug.Log(string.Format("ArgumentNullException : {0}", ane.ToString()));
        } catch (SocketException se) {

            Debug.Log(string.Format("SocketException : {0}", se.ToString()));
        } catch (Exception e) {
            Debug.Log(string.Format("Unexpected exception : {0}", e.ToString()));
        }
    }


}