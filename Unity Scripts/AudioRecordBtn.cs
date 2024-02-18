using UnityEngine;
using System.Collections;
using UnityEngine.Networking;

public class AudioRecordBtn : MonoBehaviour
{
    public MicAudio micAudio;

    void Update()
    {
        if (OVRInput.GetDown(OVRInput.Button.One))
        {
            micAudio.StartRecording();
            Debug.Log("Recording started.");
        }

        if (OVRInput.GetUp(OVRInput.Button.One))
        {
            micAudio.StopRecording();
            Debug.Log("Recording stopped, fetching base64 string.");
        }
    }
}
