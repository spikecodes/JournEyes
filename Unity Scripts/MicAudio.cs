using System;
using System.Text;
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

    public void Start() {
        var uri = new Uri("https://api.art3m1s.me/treehacks/");
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
            ReceivedText.text += "Received On " + name + " : " + response.GetValue<JToken>().ToString() + "\n";
        });
        
        Debug.Log("Connecting...");
        socket.Connect();
    }

    public void StartRecording()
    {
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
        consoleText.text = "Stopped recording.";

        // Current samples
        int position = Microphone.GetPosition(null);

        //stop recording...
        Microphone.End(null);

        // Trim the audio clip down to just the recorded part
        float[] soundData = new float[audioSource.clip.samples * audioSource.clip.channels];
        audioSource.clip.GetData(soundData, 0);
        List<float> newSoundData = new List<float>();
        for (int i = 0; i < position; i++) {
            newSoundData.Add(soundData[i]);
        }
        audioSource.clip.SetData(newSoundData.ToArray(), 0);
        audioSource.clip = AudioClip.Create("Recording", position, audioSource.clip.channels, audioSource.clip.frequency, false);
        audioSource.clip.SetData(newSoundData.ToArray(), 0);
        
        consoleText.text = "Playing...";
        
        // Play
        audioSource.Play();

        // Send audio clip over socketio byte by byte as base64 of wav
        byte[] bytes = WavUtility.FromAudioClip(audioSource.clip);
        string base64 = Convert.ToBase64String(bytes);

        // Emit it to the socket as a json object in the form {audio: [the audio base64 string], image: [the image base64 string]}
        JObject data = new JObject();
        data["audio"] = base64;
        data["image"] = "null";
        socket.Emit("audio", data);

        consoleText.text = "Sent to websocket";
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
}
