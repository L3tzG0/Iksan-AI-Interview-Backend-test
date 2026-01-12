import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
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

# Define the FastAPI Router
router = APIRouter()

executor = ThreadPoolExecutor(max_workers=10)
http_client = httpx.AsyncClient(
    timeout=None, 
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)

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

                    all_audio = b"".join(audio_chunks)

                    if not all_audio:
                        try:
                            await websocket.send_json({"type": "ERROR", "message": "No audio"})
                        except Exception as e:
                            logger.debug("Failed to send No audio ERROR to client", exc_info=e)
                        break

                    api_res = None
                    try:
                        api_res = await call_whisper_api(all_audio, "korean")
                    except Exception:
                        logger.exception("call_whisper_api failed")

                    if api_res:
                        loop = asyncio.get_event_loop()
                        payload = await loop.run_in_executor(executor, _sync_calculate_metrics, api_res)
                        await websocket.send_json(payload)
                        logger.info(f"Whisper API raw response: {api_res}")
                    else:
                        await websocket.send_json({"type": "ERROR", "message": "API Failure"})
                    break
    except WebSocketDisconnect:
        # pass
        logger.info("WebSocket disconnected by client or network before CLOSE_SIGNAL")

    finally:
        # audio_buffer.close()
        # audio_chunks.clear()
        # if websocket.client_state != WebSocketState.DISCONNECTED:
        #     await websocket.close()
        try:
            client_state = getattr(websocket, "client_state", None)
            if client_state != WebSocketState.DISCONNECTED:
                # Attempt a graceful close; wrap in try/except to avoid "Cannot call send once close was sent."
                try:
                    await websocket.close()
                except RuntimeError:
                    # this typically means the close handshake was already sent/started by the other side
                    logger.debug("websocket.close() raised RuntimeError - close already in progress")
                except Exception:
                    logger.exception("Exception while closing websocket (ignored)")
        except Exception:
            # defensive: any unexpected error in cleanup should not propagate
            logger.exception("Unexpected error during websocket cleanup (ignored)")
        logger.info("STT websocket cleanup complete")