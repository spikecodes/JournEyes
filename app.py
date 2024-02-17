from fastapi import FastAPI
from socket_wrapper import socketio_mount

import asyncio
import json
from openai import AsyncOpenAI

import dotenv
dotenv.load_dotenv()

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

