from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image
from socket_wrapper import socketio_mount
import tempfile
import os

from openai import AsyncOpenAI

import dotenv
dotenv.load_dotenv()

from segment import process_image_and_text
import io
import base64

from pydantic import BaseModel

client = AsyncOpenAI()

# Initialize FastAPI and SocketIO
app = FastAPI()
sio = socketio_mount(app)

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
    
@sio.on('event')
async def segment_image(sid, data):
    """
    Socket.IO event to handle image segmentation requests.
    Expects data to contain 'text' and 'image' (base64 encoded) keys.
    """
    text = data['text']
    image_data = data['image']
    image = process_image_and_text(text, image_data)

    # For the purpose of this example, let's convert the PIL Image back to base64 to send it back
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Emit an event back with the processed image
    await sio.emit('segmented_image', {'image': img_str}, room=sid)
    
class ImageTextRequest(BaseModel):
    base64_audio: str  # Base64 encoded audio
    image: str  # Base64 encoded image

@app.post("/process")
async def process_image(request: ImageTextRequest):
    """
    Process an image based on the provided text and return the processed image.
    The image should be provided as a base64-encoded string.
    """
    text = await transcribe_base64_audio(request.base64_audio)
    image_data = request.image

    # Decode the base64 image
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    processed_image = process_image_and_text(text, image)

    # Convert the processed image back to base64 to send back as response
    buffered = io.BytesIO()
    processed_image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return JSONResponse(content={"processed_image": img_str})

async def transcribe_base64_audio(base64_audio):
    # Check for header
    if base64_audio.startswith("data:audio/wav;base64,"):
        base64_audio = base64_audio[len("data:audio/wav;base64,"):]
    
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