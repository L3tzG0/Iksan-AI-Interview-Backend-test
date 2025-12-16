# Interview Flow - Visual Diagram

**Quick Reference Guide for Frontend Developers**

---

## Complete User Journey

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         STUDENT INTERVIEW JOURNEY                         │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────┐
│   STEP 1    │  SESSION INITIATION
│  Upload CV  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Frontend Action: POST /api/v1/interview_sessions/initiate               │
│  Request Body:                                                           │
│    - file: PDF/DOCX/TXT (or raw_text)                                  │
│    - field: "Software Engineering"                                      │
│    - role: "Backend Developer"                                          │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Backend Response: 202 ACCEPTED                                          │
│  {                                                                       │
│    "success": true,                                                      │
│    "session_id": 123,                                                    │
│    "message": "Request queued. 2 jobs ahead of you.",                   │
│    "questions": []                                                       │
│  }                                                                       │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   STEP 2    │  POLL FOR QUESTIONS (every 3 seconds)
│  Wait for   │
│  Questions  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  GET /api/v1/interview_sessions/status/{session_id}                     │
│                                                                          │
│  Response while processing:                                              │
│  {                                                                       │
│    "session_id": 123,                                                    │
│    "status": "generating",  ← "pending" → "generating"                 │
│    "is_ready": false                                                     │
│  }                                                                       │
│                                                                          │
│  ... keep polling ...                                                    │
│                                                                          │
│  Response when ready:                                                    │
│  {                                                                       │
│    "session_id": 123,                                                    │
│    "status": "in_progress",                                             │
│    "is_ready": true  ← READY! Fetch questions                          │
│  }                                                                       │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  GET /api/v1/interview_sessions/{session_id}                            │
│                                                                          │
│  Response:                                                               │
│  {                                                                       │
│    "session_id": 123,                                                    │
│    "status": "in_progress",                                             │
│    "detailed_feedback": [                                                │
│      {                                                                   │
│        "question": "Tell me about your experience with Python...",       │
│        "question_order": 1,                                              │
│        "answer": null,                                                   │
│        ...scores are null...                                             │
│      },                                                                  │
│      ... 9 more questions ...                                            │
│    ]                                                                     │
│  }                                                                       │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   STEP 3    │  ANSWER QUESTIONS (1-10)
│  Record     │
│  Answers    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  FOR EACH QUESTION (Repeat 10 times)                                     │
│                                                                          │
│  A. Connect WebSocket:  ws://host/api/v1/stt/live                       │
│                                                                          │
│  B. User clicks "Start Recording"                                        │
│     ├─ Get microphone access                                             │
│     ├─ Start MediaRecorder                                               │
│     └─ Stream audio chunks to WebSocket                                  │
│                                                                          │
│  C. Receive real-time transcription:                                     │
│     {                                                                    │
│       "transcript": "I have been working with Python",                   │
│       "is_final": false,  ← Display as interim                          │
│       "pauses": [...]                                                    │
│     }                                                                    │
│                                                                          │
│  D. User clicks "Stop Recording"                                         │
│     └─ Send: {"type": "CLOSE_SIGNAL"}                                   │
│                                                                          │
│  E. Receive final summary:                                               │
│     {                                                                    │
│       "type": "FINAL_SUMMARY",                                           │
│       "final_transcript": "I have been working with Python...",          │
│       "audio_duration_seconds": 45.2,                                    │
│       "word_count": 87,                                                  │
│       "total_pause_duration_seconds": 3.5,                               │
│       "total_pause_count": 5                                             │
│     }                                                                    │
│                                                                          │
│  F. Store answer data:                                                   │
│     answers[questionIndex] = {                                           │
│       question_order: 1,                                                 │
│       question_text: "Tell me about...",                                 │
│       answer_text: final_transcript,                                     │
│       audio_duration_seconds: 45.2,                                      │
│       word_count: 87,                                                    │
│       total_pause_duration_seconds: 3.5,                                 │
│       total_pause_count: 5                                               │
│     }                                                                    │
│                                                                          │
│  G. Move to next question OR submit if complete                          │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   STEP 4    │  SUBMIT FOR EVALUATION
│  Submit All │
│  Answers    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  POST /api/v1/interview_sessions/submit                                 │
│                                                                          │
│  Request Body:                                                           │
│  {                                                                       │
│    "session_id": 123,                                                    │
│    "qa_pairs": [                                                         │
│      {                                                                   │
│        "question_order": 1,                                              │
│        "question_text": "Tell me about...",                              │
│        "answer_text": "I have been working...",                          │
│        "audio_duration_seconds": 45.2,                                   │
│        "word_count": 87,                                                 │
│        "total_pause_duration_seconds": 3.5,                              │
│        "total_pause_count": 5                                            │
│      },                                                                  │
│      ... 9 more Q&A pairs ...                                            │
│    ]                                                                     │
│  }                                                                       │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Response: 202 ACCEPTED                                                  │
│  {                                                                       │
│    "success": true,                                                      │
│    "session_id": 123,                                                    │
│    "message": "Evaluation queued. 1 job ahead."                         │
│  }                                                                       │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   STEP 5    │  POLL FOR RESULTS (every 5 seconds)
│  Wait for   │
│ Evaluation  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  GET /api/v1/interview_sessions/status/{session_id}                     │
│                                                                          │
│  Response while processing:                                              │
│  {                                                                       │
│    "status": "evaluating",  ← "pending_evaluation" → "evaluating"      │
│    "is_ready": false                                                     │
│  }                                                                       │
│                                                                          │
│  ... keep polling ...                                                    │
│                                                                          │
│  Response when complete:                                                 │
│  {                                                                       │
│    "status": "completed",                                               │
│    "is_ready": true  ← READY! Fetch results                            │
│  }                                                                       │
└──────┬───────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   STEP 6    │  DISPLAY RESULTS
│   Show      │
│  Feedback   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  GET /api/v1/interview_sessions/{session_id}                            │
│                                                                          │
│  Response:                                                               │
│  {                                                                       │
│    "session_id": 123,                                                    │
│    "status": "completed",                                               │
│    "overall_score": 7.5,  ← Main score (0-10)                          │
│                                                                          │
│    "strength_summary": "You demonstrated strong...",                    │
│    "areas_for_growth": "Consider improving...",                         │
│                                                                          │
│    "detailed_feedback": [                                                │
│      {                                                                   │
│        "question": "Tell me about your experience...",                   │
│        "answer": "I have been working with Python...",                   │
│        "evaluation": "Your answer showed good knowledge...",             │
│        "content_relevance_score": 8.0,                                   │
│        "structure_score": 7.5,                                           │
│        "fluency_score": 7.0,                                             │
│        "confidence_score": 8.5,                                          │
│        "overall_score": 7.7,  ← Per-question score                      │
│        "is_correct": true                                                │
│      },                                                                  │
│      ... 9 more with scores ...                                          │
│    ],                                                                    │
│                                                                          │
│    "next_steps": [                                                       │
│      "Practice using the STAR method...",                                │
│      "Work on reducing filler words...",                                 │
│      "Expand your technical vocabulary..."                               │
│    ]                                                                     │
│  }                                                                       │
└──────────────────────────────────────────────────────────────────────────┘

```

## Quick Reference: Key Endpoints

```
┌──────────────────────────────────────────────────────────────────┐
│                     API QUICK REFERENCE                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SESSION INITIATION                                              │
│  POST /api/v1/interview_sessions/initiate                       │
│  → 202 Accepted {session_id}                                    │
│                                                                  │
│  STATUS CHECK                                                    │
│  GET /api/v1/interview_sessions/status/{session_id}             │
│  → 200 OK {status, is_ready}                                    │
│                                                                  │
│  GET QUESTIONS                                                   │
│  GET /api/v1/interview_sessions/{session_id}                    │
│  → 200 OK {session details + questions}                         │
│                                                                  │
│  SPEECH-TO-TEXT (WEBSOCKET)                                      │
│  WS ws://host/api/v1/stt/live                                   │
│  → Real-time transcription + final summary                       │
│                                                                  │
│  SUBMIT ANSWERS                                                  │
│  POST /api/v1/interview_sessions/submit                         │
│  → 202 Accepted {session_id}                                    │
│                                                                  │
│  GET RESULTS                                                     │
│  GET /api/v1/interview_sessions/{session_id}                    │
│  → 200 OK {scores, feedback, summary, next_steps}               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

**See [INTERVIEW_FLOW_FRONTEND_INTEGRATION.md](./INTERVIEW_FLOW_FRONTEND_INTEGRATION.md) for detailed implementation guide.**
