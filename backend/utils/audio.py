# base
import io
import os
import logging

# third-party imports
from dotenv import load_dotenv
import sounddevice as sd
from google.cloud import speech
import numpy as np
import openai
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Set your Google Cloud credentials
GOOGLE_AUDIO_TRANSCRIPTION_CREDENTIALS = os.getenv("GOOGLE_AUDIO_TRANSCRIPTION_CREDENTIALS")

def record_audio(duration, fs=16000):
    """Records audio from the microphone and return as byte string"""
    logging.info('Recording audio...')
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    byte_stream = io.BytesIO()
    np.save(byte_stream, myrecording)
    logging.info('Finished recording audio')
    byte_stream.seek(0)
    return byte_stream

def transcribe_audio(audio_stream, language_code='en-US'):
    """Transcribes audio file using Google Cloud Speech API"""

    client = speech.SpeechClient.from_service_account_json(GOOGLE_AUDIO_TRANSCRIPTION_CREDENTIALS)

    audio = speech.RecognitionAudio(content=audio_stream.read())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code)
    
    recognition_config = speech.RecognizeRequest(
        audio=audio,
        config=config
    )

    # Detects speech in the audio file
    response = client.recognize(request=recognition_config)

    for result in response.results:
        print('Transcript: {}'.format(result.alternatives[0].transcript))
        return result.alternatives[0].transcript

def transcript_classification(transcript):
    """Classifies the transcript using the GPT model"""
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"""Can you tell me if this transcript is about code or not about code? Simply reply, "code" or "not".
        ```
        {transcript}
        ```
        """,
        temperature=0.3,
        max_tokens=60
    )

    generated_text = response.choices[0].text.strip()
    if 'code' in generated_text.lower():
        return 'about code'
    else:
        return 'not about code'

if __name__ == '__main__':
    audio_stream = record_audio(10)  # records 10 seconds of audio
    transcript = transcribe_audio(audio_stream)
    print(transcript_classification(transcript))
    print("Done")