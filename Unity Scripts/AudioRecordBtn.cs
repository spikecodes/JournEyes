using UnityEngine;
using System.Collections;
using UnityEngine.Networking;

public class AudioRecordBtn : MonoBehaviour
{
    public MicAudio micAudio;

    // Update is called once per frame
    void Update()
    {
        // Start recording when the button is pressed down
        if (OVRInput.GetDown(OVRInput.Button.One))
        {
            micAudio.StartRecording();
            Debug.Log("Recording started.");
        }

        // Stop recording and take a screenshot when the button is released
        if (OVRInput.GetUp(OVRInput.Button.One))
        {
            micAudio.StopRecording();
            Debug.Log("Recording stopped, capturing screenshot.");
            StartCoroutine(CaptureScreenshotAndSend());
        }
    }

    IEnumerator CaptureScreenshotAndSend()
    {
        yield return new WaitForEndOfFrame();

        RenderTexture renderTexture = new RenderTexture(Screen.width, Screen.height, 24);
        Camera.main.targetTexture = renderTexture;
        Camera.main.Render();

        Texture2D texture = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
        RenderTexture.active = renderTexture;
        texture.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0);
        texture.Apply();

        Camera.main.targetTexture = null;
        RenderTexture.active = null; // JC: added to avoid errors
        Destroy(renderTexture);

        byte[] bytes = texture.EncodeToPNG();
        string base64String = System.Convert.ToBase64String(bytes);

        Destroy(texture); // Clean up the texture from memory after encoding

        Debug.Log("Screenshot captured, sending to backend...");
        StartCoroutine(SendScreenshot(base64String));
    }

    IEnumerator SendScreenshot(string base64String)
    {
        WWWForm form = new WWWForm();
        form.AddField("image", base64String);

        using (UnityWebRequest www = UnityWebRequest.Post("https://4bbf-2607-f6d0-ced-5b4-bcd4-1e9-1b51-86e2.ngrok-free.app/upload", form))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Failed to upload screenshot: {www.error}");
            }
            else
            {
                Debug.Log("Screenshot uploaded successfully.");
            }
        }
    }
}
