import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from deepgram import DeepgramError, LiveTranscriptionEvents
from typing import Any, List, Dict
import json
import httpx
from app.core.config import settings
import logging
import wave
import io
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Assuming app.services is accessible from app.api.v1.endpoints
from app.services.stt_service import (
    transcribe_file, 
    get_live_connection, 
    LIVE_OPTIONS,
)

# Define the FastAPI Router
router = APIRouter()

executor = ThreadPoolExecutor(max_workers=10)
http_client = httpx.AsyncClient(
    timeout=None, 
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)

# --- REST API Endpoint (File Upload) ---
@router.post(
    "/korean",
    summary="Transcribe Korean Audio File (REST)",
    response_description="Returns key transcription data as a dictionary. The 'answer_text' field contains the final transcription for database insertion."
)
async def transcribe_korean_audio_route(file: UploadFile = File(...)) -> Any:
    """
    Handles file upload for Korean transcription using Deepgram Nova-3.
    Returns a dictionary containing the transcription text (under 'answer_text') 
    and related metadata.
    """
    try:
        audio_data = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read audio file.")

    try:
        # transcribe_file returns a dictionary
        results = await transcribe_file(audio_data)
        return results
    except DeepgramError as e:
         print(f"Deepgram Client Error: {e}")
         raise HTTPException(status_code=400, detail=f"Transcription failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during transcription.")


# --- WEBSOCKET Endpoint (Live Transcription) ---

# Helper function to generate and send the final summary
async def send_final_summary(websocket: WebSocket, final_transcript_text: str, final_pauses: List[Dict], final_utterance_end_time: float, total_word_count: int):
    """Generates the final summary payload and attempts to send it to the client."""
    final_result = {
        "type": "FINAL_SUMMARY",
        "final_transcript": final_transcript_text.strip(),
        # "all_detected_pauses": final_pauses, # Optionally include full pause details
        "total_pause_duration_seconds": round(sum(p.get('gap_seconds', 0.0) for p in final_pauses), 2),
        "total_pause_count": len(final_pauses),
        "audio_duration_seconds": round(final_utterance_end_time, 2), 
        "word_count": total_word_count 
    }
    
    print("\n--- AGGREGATED FINAL TRANSCRIPTION RESULT (End of Session) ---")
    print(json.dumps(final_result, indent=2, ensure_ascii=False))
    print("---------------------------------------------")

    try:
        # Check the state again just before sending, but rely on the explicit signal
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.send_json(final_result)
            print("Sent FINAL_SUMMARY to client successfully.")
            return True
        else:
            print("Could not send FINAL_SUMMARY: WebSocket state is already DISCONNECTED.")
            return False
    except Exception as e:
        print(f"Failed to send final summary to client: {e}")
        return False
@router.websocket("/live-deepgram")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")

    dg_connection = None
    main_loop = asyncio.get_event_loop()
    
    # State variables
    last_word_end_time = 0.0
    final_transcript_text = ""
    final_pauses = [] 
    total_word_count = 0 
    final_utterance_end_time = 0.0 

    try:
        dg_connection = get_live_connection()

        def handle_deepgram_results(self, result, **kwargs):
            nonlocal last_word_end_time, final_transcript_text, final_pauses
            nonlocal total_word_count, final_utterance_end_time
            
            try:
                if not result.channel.alternatives:
                    return

                alt = result.channel.alternatives[0]
                text = alt.transcript 
                
                if not text:
                    return
                
                words = getattr(alt, "words", None)
                pauses = []
                
                # A. INTER-PACKET PAUSE DETECTION
                if words and len(words) > 0 and last_word_end_time > 0.0:
                    first_word_start = words[0].start
                    gap_to_first_word = first_word_start - last_word_end_time
                    
                    if gap_to_first_word > 0.5:
                        inter_pause = {
                            "after_word": "PREVIOUS_UTTERANCE",
                            "before_word": words[0].word,
                            "gap_seconds": round(gap_to_first_word, 2),
                            "type": "inter-packet"
                        }
                        pauses.append(inter_pause)
                        final_pauses.append(inter_pause)
                    
                # B. INTRA-PACKET PAUSE DETECTION
                if words and len(words) > 1:
                    for i in range(1, len(words)):
                        prev_end = words[i-1].end
                        curr_start = words[i].start
                        gap = curr_start - prev_end
                        
                        if gap > 0.3:
                            intra_pause = {
                                "after_word": words[i-1].word, 
                                "before_word": words[i].word,
                                "gap_seconds": round(gap, 2),
                                "type": "intra-packet"
                            }
                            pauses.append(intra_pause)
                            final_pauses.append(intra_pause)
                            
                
                # === Update the persistent state and final accumulation ===
                if words and len(words) > 0:
                    last_word_end_time = words[-1].end
                    
                    if result.is_final:
                        final_transcript_text += text + " "
                        total_word_count += len(words)
                        final_utterance_end_time = max(final_utterance_end_time, words[-1].end)
                
                # Send back the results for real-time display
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json(
                        {
                            "transcript": text,
                            "is_final": result.is_final,
                            "pauses": pauses
                        }
                    ),
                    main_loop
                )

            except Exception as e:
                print(f"Error in deepgram handler (scheduling send): {e}")

        # 3. Attach event handler
        dg_connection.on(LiveTranscriptionEvents.Transcript, handle_deepgram_results)
        
        # 4. Start the Deepgram connection
        if dg_connection.start(LIVE_OPTIONS) is False:
            print("Failed to start Deepgram Live connection.")
            raise Exception("Deepgram Live connection failed to initialize.")

        # 5. Receive audio or control messages from client
        while True:
            try:
                message = await websocket.receive()
                
                if "bytes" in message:
                    # Received audio chunk
                    dg_connection.send(message["bytes"])
                
                elif "text" in message:
                    # Received a text/JSON control message
                    control_message = json.loads(message["text"])
                    
                    if control_message.get("type") == "CLOSE_SIGNAL":
                        print("Received CLOSE_SIGNAL from client.")
                        
                        # Execute final summary logic and send response while connection is active
                        await send_final_summary(
                            websocket, 
                            final_transcript_text, 
                            final_pauses, 
                            final_utterance_end_time, 
                            total_word_count
                        )
                        # Gracefully exit the loop
                        break 
                        
            except WebSocketDisconnect:
                # This handles cases where the client disconnected unexpectedly without the signal
                print("WebSocket disconnected unexpectedly by client.")
                break
            except Exception as e:
                print(f"Error receiving from client: {e}")
                break
            
    except DeepgramError as e:
        print(f"Deepgram Client Error during live transcription: {e}")
    except Exception as e:
        print(f"Unexpected error in live transcription endpoint: {e}")
    finally:
        # Cleanup Deepgram connection
        if dg_connection and hasattr(dg_connection, 'finish'):
            print("Closing Deepgram connection.")
            dg_connection.finish() 
        
        # Cleanup FastAPI/Starlette WebSocket connection
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
            print("WebSocket connection closed.")
        else:
            print("WebSocket connection already closed.")


WHISPER_API_BASE_URL = settings.WHISPER_BASE_URL
WHISPER_API_KEY = settings.ELICE_API_KEY

@router.post(
    "/whisper-korean",
    summary="Transcribe Korean using Whisper-large-v3",
    response_description="Returns transcribed text and word-level timestamps."
)
async def transcribe_korean_whisper(file: UploadFile = File(...)) -> Any:
    """
    Handles audio transcription using the company's Whisper-large-v3 service.
    Follows Page 1 Documentation:
    - Path: /transcribe
    - Audio Field: 'audio'
    - Includes word-level timestamps and Korean language setting.
    """
    # url = f"{WHISPER_API_BASE_URL}/transcribe"
    url = f"{WHISPER_API_BASE_URL}/transcribe"
    
    # Note: Your docs mention "application/json" content-type in the example,
    # but also use multipart/form-data (-F). We include it as requested in docs.
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {WHISPER_API_KEY}"
    }

    try:
        # Read the uploaded file into memory
        audio_content = await file.read()
        
        # Prepare the multipart payload
        # 'audio' is the key expected by the server
        files = {
            'audio': (file.filename, audio_content, file.content_type or 'audio/mpeg')
        }
        
        # Metadata parameters
        data = {
            # 'return_timestamps': True, # Sent as string 'true' for multipart
            'return_timestamps': 'word',
            'language': 'korean'
            # 'initial_prompt': 'This is a Korean interview for a job position.'
        }

        async with httpx.AsyncClient() as client:
            # We set timeout to None because Whisper-large-v3 can be slow 
            # and we want to avoid the ReadTimeout you saw earlier.
            response = await client.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=None 
            )

            # Check for errors from the company server
            if response.status_code != 200:
                logger.error(f"Whisper Server Error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Upstream STT Error: {response.text}"
                )

            result = response.json()
            
            # Basic validation of response structure
            if "_result" in result and result["_result"].get("status") != "ok":
                logger.warning(f"Whisper returned status: {result['_result'].get('reason')}")

            return result

    except httpx.ConnectError:
        logger.error("Failed to connect to the Whisper API server.")
        raise HTTPException(status_code=503, detail="Transcription service is unreachable.")
    
    except Exception as e:
        logger.error(f"Unexpected error in whisper_transcribe: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during transcription.")

def _sync_create_wav_bytes(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """Wraps raw PCM into a standard WAV container."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return buffer.getvalue()

async def call_whisper_api(audio_bytes: bytes, language: str = "korean") -> Any:
    """Sends WAV-encoded audio to the Whisper server."""
    loop = asyncio.get_event_loop()

    # Wrap with 16kHz header (matching forced frontend rate)
    # wav_data = create_wav_bytes(audio_bytes, 16000)
    wav_data = await loop.run_in_executor(executor, _sync_create_wav_bytes, audio_bytes, 16000)
    
    url = f"{WHISPER_API_BASE_URL}/transcribe"
    headers = {
        "Authorization": f"Bearer {WHISPER_API_KEY}",
        "accept": "application/json"
    }
    
    files = {'audio': ('audio.wav', wav_data, 'audio/wav')}
    data = {'return_timestamps': 'word', 'language': language}

    try:
        # Uses the shared connection pool
        response = await http_client.post(url=url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Whisper API Error: {e}")
        return None
    
    # async with httpx.AsyncClient() as client:
    #     try:
    #         response = await client.post(url, headers=headers, files=files, data=data, timeout=None)
    #         response.raise_for_status()
    #         return response.json()
    #     except Exception as e:
    #         logger.error(f"Whisper API Error: {e}")
    #         return None

def _sync_calculate_metrics(api_res: Dict) -> Dict:
    """Calculates summary and pauses from Whisper word-level data."""
    if not api_res or api_res.get("_result", {}).get("status") != "ok":
        return {"type": "ERROR", "message": "Transcription failed"}

    transcript = api_res.get("transcript", {})
    chunks = transcript.get("chunks", [])
    full_text = transcript.get("text", "").strip()

    pauses = []
    total_words = 0
    last_end = 0.0
    max_dur = 0.0

    for chunk in chunks:
        word = chunk.get("text", "").strip()
        if not word: continue

        ts = chunk.get("timestamp", [0.0, 0.0])
        start, end = ts[0], ts[1]

        total_words += 1
        max_dur = max(max_dur, end)

        if last_end > 0:
            gap = start - last_end
            if gap > 0.6: # Filter for significant pauses
                pauses.append({
                    "before_word": word,
                    "gap_seconds": round(gap, 2)
                })
        last_end = end

    return {
        "type": "FINAL_SUMMARY",
        "final_transcript": full_text,
        "total_pause_duration_seconds": round(sum(p['gap_seconds'] for p in pauses), 2),
        "total_pause_count": len(pauses),
        "audio_duration_seconds": round(max_dur, 2),
        "word_count": total_words,
        # "all_detected_pauses": pauses
    }

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # audio_buffer = io.BytesIO()
    audio_chunks = []

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                # audio_buffer.write(message["bytes"])
                audio_chunks.append(message["bytes"])

            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "CLOSE_SIGNAL":
                    # audio_buffer.seek(0)
                    # all_audio = audio_buffer.read()
                    all_audio = b"".join(audio_chunks)

                    if not all_audio:
                        await websocket.send_json({"type": "ERROR", "message": "No audio"})
                        break

                    api_res = await call_whisper_api(all_audio, "korean")
                    if api_res:
                        loop = asyncio.get_event_loop()
                        payload = await loop.run_in_executor(executor, _sync_calculate_metrics, api_res)
                        await websocket.send_json(payload)
                        logger.info(f"Whisper API raw response: {api_res}")
                    else:
                        await websocket.send_json({"type": "ERROR", "message": "API Failure"})
                    break
    except WebSocketDisconnect:
        pass
    finally:
        # audio_buffer.close()
        audio_chunks.clear()
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()