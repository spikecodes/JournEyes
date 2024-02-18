from fastapi import FastAPI
from socket_wrapper import socketio_mount

import asyncio
import json
from openai import AsyncOpenAI

import dotenv
dotenv.load_dotenv()

from segment import process_image_and_text
import io
import base64

client = AsyncOpenAI()

# Initialize FastAPI and SocketIO
app = FastAPI()
sio = socketio_mount(app)

@app.route('/')
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
    image = await process_image_and_text(text, image_data)

    # For the purpose of this example, let's convert the PIL Image back to base64 to send it back
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Emit an event back with the processed image
    await sio.emit('segmented_image', {'image': img_str}, room=sid)
