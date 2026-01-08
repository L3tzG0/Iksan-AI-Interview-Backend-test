import os
import sys
import asyncio
import time
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    LiveOptions, 
    FileSource,
    DeepgramError,
    LiveTranscriptionEvents,
    LiveResultResponse,
)
# from dotenv import load_dotenv
from app.core.config import settings 

# Load environment variables
# load_dotenv() 
# DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
# deepgram_client = None

DEEPGRAM_API_KEY = settings.DEEPGRAM_API_KEY
deepgram_client = None
# --- Client and Health Check Setup ---

def initialize_deepgram_client():
    """Initializes the Deepgram client and performs a health check."""
    global deepgram_client
    if not DEEPGRAM_API_KEY:
        print("\n!!! FATAL CONFIGURATION ERROR !!!")
        print("ERROR: DEEPGRAM_API_KEY environment variable is missing or empty.")
        sys.exit(1)

    try:
        deepgram_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
        print("DEBUG: Deepgram Client object initialized.")
        
        # Health Check: Use a synchronous authenticated call to verify key/connectivity
        print("\nRunning Deepgram API Health Check (Verifying Key and Connectivity)...")
        deepgram_client.manage.v("1").get_models()
        print("DIAGNOSTIC SUCCESS: Deepgram API key is valid and network connection established.")
        
    except DeepgramError as e:
        print("\n!!! DIAGNOSTIC FAILED !!!")
        print("ERROR: Deepgram API Key is invalid or connection failed.")
        print(f"Deepgram Error Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"DIAGNOSTIC FAILED: An unexpected error occurred: {e}")
        sys.exit(1)

# Initialize the client immediately when the service file is loaded
initialize_deepgram_client()

# --- Configuration Constants ---
LIVE_OPTIONS = LiveOptions(
    model="nova-3",
    language="ko",
    punctuate=True,
    encoding="linear16",
    sample_rate=16000,
    channels=1,
    interim_results=True,
    utterance_end_ms="1000",
    vad_events=True,
)

PRERECORDED_OPTIONS = PrerecordedOptions(
    model="nova-3",
    language="ko",
    punctuate=True,
    diarize=False,
)

# --- Service Functions ---

async def transcribe_file(audio_data: bytes) -> dict:
    """
    Handles the prerecorded file transcription logic and returns a dictionary 
    with key transcription details for direct use in the API or database.
    """
    if not deepgram_client:
        raise Exception("Deepgram client not initialized.")

    payload: FileSource = {"buffer": audio_data}
    start_time = time.perf_counter()
    
    response = deepgram_client.listen.prerecorded.v("1").transcribe_file(
        payload,
        options=PRERECORDED_OPTIONS,
    )

    end_time = time.perf_counter()
    processing_time_ms = int((end_time - start_time) * 1000)

    # Process response structure
    transcript = response.results.channels[0].alternatives[0].transcript
    confidence = response.results.channels[0].alternatives[0].confidence
    duration = response.metadata.duration

    # Return a dictionary structure directly
    return {
        "answer_text": transcript, # Use the target DB column name for clarity
        "confidence": confidence,
        "model_used": PRERECORDED_OPTIONS.model,
        "language": PRERECORDED_OPTIONS.language,
        "duration_seconds": duration,
        "processing_time_ms": processing_time_ms
    }

def get_live_connection():
    """Returns a new live connection instance."""
    if not deepgram_client:
        raise Exception("Deepgram client not initialized.")
    return deepgram_client.listen.live.v("1")