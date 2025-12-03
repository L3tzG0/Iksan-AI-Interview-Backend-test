import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from deepgram import DeepgramError, LiveTranscriptionEvents
from typing import Any, List, Dict
import json

# Assuming app.services is accessible from app.api.v1.endpoints
from app.services.stt_service import (
    transcribe_file, 
    get_live_connection, 
    LIVE_OPTIONS,
)

# Define the FastAPI Router
router = APIRouter()

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
@router.websocket("/live")
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