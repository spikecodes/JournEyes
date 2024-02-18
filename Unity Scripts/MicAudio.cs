using System;
using System.Text;
using System.Collections;
using UnityEngine.Networking;
using System.Collections.Generic;
using SocketIOClient;
using SocketIOClient.Newtonsoft.Json;
using UnityEngine;
using UnityEngine.UI;
using Newtonsoft.Json.Linq;
using TMPro; // Make sure to include the TextMeshPro namespace

public class MicAudio : MonoBehaviour {
    public TMP_Text consoleText;
    public TMP_Text ReceivedText;
    private SocketIOUnity socket;
    bool isRecording = false;
    public AudioSource audioSource;
    private string fetchUrl = "https://21ec-2607-f6d0-ced-5b4-352c-f7a0-97aa-c2c8.ngrok-free.app/screenshot";
    private string sendUrl = "https://21ec-2607-f6d0-ced-5b4-352c-f7a0-97aa-c2c8.ngrok-free.app/upload";

    public void Start() {
        // URL to fetch the screenshot from the Flask backend


        var uri = new Uri("https://21ec-2607-f6d0-ced-5b4-352c-f7a0-97aa-c2c8.ngrok-free.app/");
        socket = new SocketIOUnity(uri);

        ///// reserved socketio events
        socket.OnConnected += (sender, e) =>
        {
            Debug.Log("socket.OnConnected");
        };
        socket.OnPing += (sender, e) =>
        {
            Debug.Log("Ping");
        };
        socket.OnPong += (sender, e) =>
        {
            Debug.Log("Pong: " + e.TotalMilliseconds);
        };
        socket.OnDisconnected += (sender, e) =>
        {
            Debug.Log("disconnect: " + e);
        };
        socket.OnAnyInUnityThread((name, response) =>
        {
            ReceivedText.text += response.GetValue<string>();
        });
        
        Debug.Log("Connecting...");
        socket.Connect();
    }

    public void StartRecording()
    {
        ReceivedText.text = "Processing...";
        consoleText.text = "Started recording...";

        Debug.Log("Devices");
        Debug.Log(Microphone.devices);

        if (Microphone.devices.Length == 0)
        {
            Debug.Log("No microphone found");
            return;
        }
        //start recording to the audio clip
        audioSource.clip = Microphone.Start(null, true, 500, 44100);
    }

    public void StopRecording()
    {
        consoleText.text = "Stopping recording...";

        // Stop microphone recording
        int position = Microphone.GetPosition(null);
        Microphone.End(null);

        // Trim the AudioClip to just the portion that was used
        float[] soundData = new float[audioSource.clip.samples * audioSource.clip.channels];
        audioSource.clip.GetData(soundData, 0);
        List<float> trimmedSoundData = new List<float>();
        for (int i = 0; i < position; i++)
        {
            trimmedSoundData.Add(soundData[i]);
        }
        AudioClip trimmedClip = AudioClip.Create("Recording", position, audioSource.clip.channels, audioSource.clip.frequency, false);
        trimmedClip.SetData(trimmedSoundData.ToArray(), 0);

        // Play the trimmed clip
        audioSource.clip = trimmedClip;
        //audioSource.Play();
        consoleText.text = "Playing back recording...";

        // Convert the audio clip to a base64 string
        byte[] audioBytes = WavUtility.FromAudioClip(trimmedClip);
        string audioBase64 = Convert.ToBase64String(audioBytes);

        // Start coroutine to fetch the screenshot, convert it to base64, and emit both audio and image
        StartCoroutine(FetchScreenshotAndSend(audioBase64));
    }

    IEnumerator FetchScreenshotAndSend(string audioBase64)
    {
        using (UnityWebRequest www = UnityWebRequest.Get(fetchUrl))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Error fetching screenshot: " + www.error);
                // Consider how you want to handle the error. For now, we'll just log it.
            }
            else
            {
                // Successfully fetched the screenshot, convert it to string
                byte[] imageBytesOfBase64String = www.downloadHandler.data;
                // Convert to string
                string imageBase64 = System.Text.Encoding.ASCII.GetString(imageBytesOfBase64String);

                consoleText.text = imageBase64;

                // Prepare the JSON object with both audio and image data in base64 format
                JObject data = new JObject();
                data["audio"] = audioBase64;
                data["image"] = imageBase64; // Replace "null" with the actual image base64 string

                // Emit the data
                using (UnityWebRequest www2 = new UnityWebRequest(fetchUrl.Replace("screenshot", "segment-image"), "POST"))
                {
                    byte[] bodyRaw = Encoding.UTF8.GetBytes(data.ToString());
                    www2.uploadHandler = new UploadHandlerRaw(bodyRaw);
                    www2.downloadHandler = new DownloadHandlerBuffer();
                    www2.SetRequestHeader("Content-Type", "application/json");

                    yield return www2.SendWebRequest();

                    if (www2.result != UnityWebRequest.Result.Success)
                    {
                        Debug.LogError("Error fetching response: " + www2.error);
                    }
                    else
                    {
                        consoleText.text = "bytes received.";
                        string response = www2.downloadHandler.text;

                        ReceivedText.text = response;
                        consoleText.text = "Received data";
                    }
                }
                consoleText.text = "Data sent to websocket.";
            }
        }
    }


    public void ToggleRecording()
    {
        isRecording = !isRecording;
        Debug.Log(isRecording == true ? "Is Recording" : "Off");

        if (isRecording) {
            StartRecording();
        } else {
            StopRecording();
        }

    }

    //IEnumerator SendBase64StringToBackend(string base64String)
    //{
    //    WWWForm form = new WWWForm();
    //    form.AddField("image", base64String);

    //    using (UnityWebRequest www = UnityWebRequest.Post(sendUrl, form))
    //    {
    //        yield return www.SendWebRequest();

    //        if (www.result != UnityWebRequest.Result.Success)
    //        {
    //            Debug.LogError($"Failed to send base64 string to backend: {www.error}");
    //        }
    //        else
    //        {
    //            Debug.Log("Base64 string sent to backend successfully.");
    //        }
    //    }
    //}
}
