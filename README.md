![Thumbnail (1)](https://github.com/spikecodes/JournEyes/assets/19519553/e1c308ae-4495-4e9b-9b33-09f2d4705afb)

# JournEyes

AI-infused VR travel assistant, to explore language, culture, and life.

> Built for [TreeHacks 2024](https://treehacks-2024.devpost.com/).

### Inspiration

Have you ever found yourself wandering in a foreign land, eyes wide with wonder, yet feeling that pang of curiosity about the stories behind the unfamiliar sights and sounds? That's exactly where we found ourselves. All four of us share a deep love for travel and an insatiable curiosity about the diverse cultures, breathtaking scenery, and intriguing items we encounter abroad. It sparked an idea: why not create a travel companion that not only shares our journey but enhances it? Enter our brainchild, a fusion of VR and AI designed to be your personal travel buddy. Imagine having a friend who can instantly transcribe signs in foreign languages, identify any object from monuments to local flora, and guide you through the most bewildering of environments. That's what we set out to build—a gateway to a richer, more informed travel experience.

### What it does

Picture this: you're standing before a captivating monument, curiosity bubbling up. With our VR travel assistant, simply speak your question, and it springs into action. This clever buddy captures your voice, processes your command, and zooms in on the object of your interest in the video feed. Using cutting-edge image search, it fetches information about just what you're gazing at. Wondering about that unusual plant or historic site? Ask away, and you'll have your answer. It's like having a local guide, historian, and botanist all rolled into one, accessible with just a glance and a word.

### How we built it

Diving into the unknown, we embarked on our development journey with Unity and the Meta XR SDK for the VR magic, while the brains of the operation—a server built with Python, FastAPI, and a sprinkle of AI wizardry—handled the heavy lifting. We tapped into Google Lens through the SERP API for unmatched image recognition and employed OpenAI's Whisper for flawless voice transcription. A breakthrough research paper from Meta allowed us to smartly crop images to focus solely on the mentioned object, directing the inquiry through our powerful agent to the relevant AI model for a swift, accurate response. This entire setup was neatly packaged with Docker and linked via ngrok, creating a seamless bridge between the VR app and our server, all while maintaining real-time interaction through websockets and the SocketIO library.

![architecture](https://i.ibb.co/cLqW8k3/architecture.png)

### Challenges we ran into

None of us had much or any experience with both Unity3D and developing VR applications so there were many challenges in learning how to use the Meta XR SDK and how to build a VR app in general. Additionally, Meta imposed a major restriction that added to the complexity of the application: we could not capture the passthrough video feed through any third-party screen recording software. This meant we had to, in the last few hours of the hackathon, create a new server in our network that would capture the casted video feed from the headset (which had no API) and then send it to the backend. This was a major challenge and we are proud to have overcome it.

### Accomplishments that we're proud of

From web developers to VR innovators, we've journeyed into uncharted territories, crafting a VR application that's not just functional but truly enriching for the travel-hungry soul. Our creation stands as a beacon of what's possible, painting a future where smart glasses serve as your personal AI-powered travel guides, making every journey an enlightening exploration.

### What we learned

The journey was as rewarding as the destination. We mastered the integration of Meta Quest 2s and 3s with Unity, weaving through the intricacies of Meta XR SDKs. Our adventure taught us to make HTTP calls within Unity, transform screenshots into Base64 strings, and leverage Google Cloud for image hosting, culminating in real-time object identification through Google Lens. Every challenge was a lesson, turning us from novices into seasoned navigators of VR development and AI integration.
