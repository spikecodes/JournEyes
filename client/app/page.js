'use client'

import {useState, useRef, useEffect} from 'react'
import {useRouter} from 'next/navigation'

import io from 'socket.io-client'
// import Audio from "@/assets/audio.svg";
let RecordRTC
const socket = io('https://8d74cc6176ee.ngrok.app/')
export default function RecordForm() {
  const router = useRouter()

  const [recording, setRecording] = useState(false)
  const [audio, setAudio] = useState(null)
  const [image, setImage] = useState(null)

  useEffect(() => {
    if (socket) {
      // Listen to an event, for example, 'message'
      socket.on('text', (data) => {
        console.log(data)
      })

      // Clean up event listener on component unmount
      return () => {
        socket.off('text')
      }
    }
  }, [socket])

  // Recording states
  const recorder = useRef(null)
  const microphone = useRef(null)

  useEffect(() => {
    import('recordrtc').then((r) => {
      RecordRTC = r.default
    })

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [recording])

  const handleKeyDown = (event) => {
    if (event.code === 'Space') {
      if (recording) {
        stopRecording()
      } else {
        startRecording()
      }
    }
  }

  const handleImageUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        // This will log the base64 string of the image
        setImage(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const captureMicrophone = async (callback) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({audio: true})
      callback(stream)
    } catch (error) {
      alert('Unable to access your microphone.')
      console.error(error)
    }
  }

  const startRecording = async () => {
    if (!recording) {
      await captureMicrophone((stream) => {
        microphone.current = stream

        const options = {
          // Required format for speech to text, 16k mono channel
          type: 'audio',
          recorderType: RecordRTC.StereoAudioRecorder,
          desiredSampRate: 16000,
          numberOfAudioChannels: 1,
        }

        recorder.current = RecordRTC(stream, options)
        console.log(recorder.current)
        recorder.current.startRecording()
        recorder.current.microphone = microphone.current

        setRecording(true)
      })
    }
  }

  const stopRecordingCallback = () => {
    console.log(recorder.current)
    const audioBlob = recorder.current.getBlob()
    setRecording(false)
    const reader = new FileReader()
    reader.readAsDataURL(audioBlob)
    reader.onloadend = () => {
      let base64Audio = reader.result

      setAudio(base64Audio)
    }
  }

  const sendAudioToServer = async () => {
    socket.emit('event', {audio: audio, image: image})
  }

  const stopRecording = () => {
    if (recorder.current) {
      recorder.current.stopRecording(stopRecordingCallback)
    }
  }

  return (
    <div className="flex flex-col text-[16px] font-normal pb-[2rem] md:pb-0">
      <div className="flex flex-col h-full max-w-[18rem]">
        <div className="flex items-center mt-[2rem] gap-[1rem]">
          {recording ? (
            <button
              onClick={() => {
                setRecording(!recording)
                stopRecording()
              }}
              className="font-bold px-[1rem] w-[64px] bg-purple hover:bg-bgwhite transition-all h-[48px] rounded-[8px] border border-black text-[#FFFFFF]"
            >
              recording{' '}
            </button>
          ) : (
            <button
              onClick={() => {
                setRecording(!recording)
                startRecording()
              }}
              className="font-bold px-[1rem] w-[64px] bg-bgwhite hover:bg-purple transition-all h-[48px] rounded-[8px] border border-black text-[#FFFFFF]"
            >
              record{' '}
            </button>
          )}
          {recording && <div className="text-purple">Recording...</div>}
        </div>
      </div>

      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="mt-[2rem]"
      />

      <button
        onClick={() => {
          console.log('Sending')
          sendAudioToServer()
        }}
        className="font-bold bg-black hover:bg-purple transition-all w-[176px] h-[56px] rounded-[8px] mt-[2rem] text-[#FFFFFF]"
      >
        Send
      </button>
    </div>
  )
}
