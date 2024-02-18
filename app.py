from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from PIL import Image
from socket_wrapper import socketio_mount
import tempfile
import os
from agent import Agent

from openai import AsyncOpenAI

from langchain.tools import tool

import websockets
from websockets.sync.client import connect

import dotenv
dotenv.load_dotenv()

from segment import process_image_and_text
from google_lens import google_lens_search
import io
import base64
import json

from pydantic import BaseModel

client = AsyncOpenAI()

# Initialize FastAPI and SocketIO
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
sio = socketio_mount(app)
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
voice = {
    "voice_id": "EXAVITQu4vr4xnSDxMaL",
    "name": "Bella",
    "settings": {
        "stability": 0.72,
        "similarity_boost": 0.2,
        "style": 0.0,
        "use_speaker_boost": False,
        "speaking_rate": 2,
    },
}
model = {
            "model_id": "eleven_multilingual_v2",
        }

current_image = None



@tool
def google_lens_wrapper(text: str) -> str:
    """
    Performs a google lens search on the current image for object detection.
    
    Input:
    - text: a short description of the object to search for.

    Returns: The result of the google lens search.
    """
    try:
        print("Cropping image based on text:", text)
        global current_image
        # Remove header if present
        if ';base64,' in current_image:
            current_image = current_image.split(';base64,')[1]
        # Decode the base64 image
        image_bytes = base64.b64decode(current_image)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        print("Image opened")

        processed_image = process_image_and_text(text, image)
        print("Image processed")

        # Convert the processed image back to base64 to send back as response
        buffered = io.BytesIO()
        processed_image.save(buffered, format="JPEG")
        current_image = base64.b64encode(buffered.getvalue()).decode()
        return google_lens_search(current_image)
    except Exception as e:
        return f"Error: {e}"
@tool
async def vision_llm(text: str) -> str:
    """
    Uses the OPENAI Vision API to answer a question based on the input image.
    
    Input:
    - text: a question about the image.
    
    Returns: The answer to the question based on the image.
    """
    global current_image
    
    response = await client.chat.completions.create(
        model="gpt-4-vision-preview",
        temperature=0,
        max_tokens=500,
        messages = [
            {
                'role': 'user',
                "content": [
                    {"type": "text", "text": "What’s in this image?"},
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": current_image,
                    },
                    },
                ],
            }
        ]
    )
    
    return response.choices[0].message.content
    
from langchain.agents import Tool
from langchain.tools import tool

from langchain_community.utilities import GoogleSerperAPIWrapper
    
search = GoogleSerperAPIWrapper()
google_search = Tool(
            name="google_search",
            func=search.run,
            description="Searches Google for the input query",
)


@app.get('/')
def index():
    return "Audio Transcription Service"
  
# Define SocketIO events
@sio.on('connect')
async def connect(sid, environ):
    print("Client connected", sid) 

@sio.on('disconnect')
async def disconnect(sid):
    print("Client disconnected", sid)

tools = [google_lens_wrapper, google_search, vision_llm]
agent = Agent(tools)
@sio.on('event')
async def segment_image(sid, data):
    """
    Socket.IO event to handle image segmentation requests.
    Expects data to contain 'text' and 'image' (base64 encoded) keys.
    """
    audio = data['audio']
    image_data = data['image']
    global current_image
    current_image = image_data
    
    text = await transcribe_base64_audio(audio)
    print("Transcribed text:", text)
    
    async def stream_response():
        async for content in agent.invoke(text):
            await sio.emit('text', content)
            
    await stream_response()
    
@sio.on('event_audio')
async def segment_image(sid, data):
    """
    Socket.IO event to handle image segmentation requests.
    Expects data to contain 'text' and 'image' (base64 encoded) keys.
    """
    audio = data['audio']
    image_data = data['image']
    global current_image
    current_image = image_data
    
    text = await transcribe_base64_audio(audio)
    print("Transcribed text:", text)
    
    async def generate_stream_input(first_text_chunk, text_generator, voice, model):
        BOS = json.dumps(
            dict(
                text=" ",
                try_trigger_generation=True,
                voice_settings=voice["settings"],
                generation_config=dict(chunk_length_schedule=[50]),
            )
        )
        EOS = json.dumps({"text": ""})

        with connect(
            f"""wss://api.elevenlabs.io/v1/text-to-speech/{voice["voice_id"]}/stream-input?model_id={model["model_id"]}""",
            additional_headers={
                "xi-api-key": elevenlabs_api_key,
            },
        ) as websocket:
            websocket.send(BOS)

            # Send the first text chunk immediately
            first_data = dict(text=first_text_chunk, try_trigger_generation=True)
            websocket.send(json.dumps(first_data))

            # Stream text chunks and receive audio
            async for text_chunk in text_chunker(text_generator):
                data = dict(text=text_chunk, try_trigger_generation=True)
                websocket.send(json.dumps(data))
                await sio.emit('text', text_chunk)
                try:
                    data = json.loads(websocket.recv(1e-4))
                    if data["audio"]:
                        await sio.emit('audio', base64.b64decode(data["audio"]))  # type: ignore
                except TimeoutError:
                    pass

            websocket.send(EOS)

            while True:
                try:
                    data = json.loads(websocket.recv())
                    if data["audio"]:
                        sio.emit('audio', base64.b64decode(data["audio"]))   # type: ignore
                except websockets.exceptions.ConnectionClosed:
                    break
                
    text_generator = agent.invoke(text)
    first_text_chunk = await text_generator.__anext__()
    await generate_stream_input(first_text_chunk, text_generator, voice, model)
                
        
    
    
class ImageTextRequest(BaseModel):
    base64_audio: str  # Base64 encoded audio
    image: str  # Base64 encoded image

@app.post("/process")
async def process_image(request: ImageTextRequest):
    """
    Process an image based on the provided text and return the processed image.
    The image should be provided as a base64-encoded string.
    """
    global current_image
    current_image = request.image
    text = await transcribe_base64_audio(request.base64_audio)
    print("Transcribed text:", text)
    
    tools = [google_lens_wrapper]
   
    agent = Agent(tools)
    
    async def stream_response():
        async for content in agent.invoke(text):
            yield content  # This streams back each piece of content generated by invoke

    return StreamingResponse(stream_response(), media_type="text/plain")

async def transcribe_base64_audio(base64_audio):
    # Check for header
    if base64_audio.startswith("data:audio/wav;base64,"):
        base64_audio = base64_audio.split(",", 1)[1]  # Ensure we remove the entire header
    
    # Decode the base64 audio to binary
    audio_data = base64.b64decode(base64_audio)

    # Create a temporary file to store the decoded audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
        temp_audio_file.write(audio_data)
        temp_file_name = temp_audio_file.name
    
    # Now that the audio is saved to a file, transcribe it
    try:
        with open(temp_file_name, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )
    finally:
        os.remove(temp_file_name)  # Ensure the temporary file is deleted
    
    return transcript

async def text_chunker(chunks):
    """Used during input streaming to chunk text blocks and set last char to space"""
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    buffer = ""
    async for text in chunks:
        if buffer.endswith(splitters):
            yield buffer if buffer.endswith(" ") else buffer + " "
            buffer = text
        elif text.startswith(splitters):
            output = buffer + text[0]
            yield output if output.endswith(" ") else output + " "
            buffer = text[1:]
        else:
            buffer += text
    if buffer != "":
        yield buffer + " "
