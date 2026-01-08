# Concurrency Flow Visualization

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USERS / CLIENTS                              │
│                  (Multiple concurrent requests)                      │
└─────────────────┬──────────────────┬──────────────────┬─────────────┘
                  │                  │                  │
                  ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                              │
│        (Handles all requests concurrently via asyncio)              │
│                                                                      │
│  Request 1 ──→ Queue Job1 (session_1) to Redis                     │
│  Request 2 ──→ Queue Job2 (session_2) to Redis                     │
│  Request 3 ──→ Queue Job3 (session_3) to Redis                     │
└─────────────┬───────────────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      REDIS QUEUE                                    │
│                  (FIFO Job Buffer)                                  │
│  [Job1] [Job2] [Job3] [Job4] ...                                   │
└─────────────┬───────────────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────────────┐
│            BACKGROUND WORKER (scripts/worker.py)                   │
│        (Single process, but async execution via asyncio)            │
│                                                                      │
│  while True:                                                        │
│    1. Apply Rate Limit (wait if needed)                            │
│    2. Pull ONE job from Redis (BLPOP with 5s timeout)              │
│    3. Schedule job as asyncio.create_task() ← NON-BLOCKING!        │
│    4. Loop back immediately to pull next job                       │
│                                                                      │
│  Background Tasks Running Concurrently:                            │
│    ├─ Task 1: Processing Job1 (LLM + DB updates)                  │
│    ├─ Task 2: Processing Job2 (LLM + DB updates)                  │
│    ├─ Task 3: Processing Job3 (LLM + DB updates)                  │
│    └─ Task N: Processing JobN (LLM + DB updates)                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
              │
              ↓
       [Database Updates]
```

---

## Timeline Visualization - Multiple Concurrent Jobs

```
TIME (seconds) →

REQUEST PHASE (FastAPI):
t=0.0   User1 submits interview request
        └─→ Creates Job1 in Redis
        └─→ Returns immediately to User1 (async HTTP response)

t=0.1   User2 submits interview request  
        └─→ Creates Job2 in Redis
        └─→ Returns immediately to User2 (async HTTP response)

t=0.2   User3 submits interview request
        └─→ Creates Job3 in Redis
        └─→ Returns immediately to User3 (async HTTP response)

---

WORKER PHASE (Background Process - Rate Limited every 7 seconds):

Worker pulls jobs from Redis at 7-second intervals
Each job is scheduled as a non-blocking asyncio task

t=1.0   [PULL PHASE] Worker pulls Job1 from Redis
        └─→ asyncio.create_task(process_interview_job(Job1))
        └─→ Worker doesn't wait - returns to queue immediately
        └─→ Next allowed pull: t=8.0

        [BACKGROUND TASK] Job1 starts executing
        ├─ t=1.1: RAG query (async, ~2 seconds)
        ├─ t=3.1: LLM generation (async, ~4-6 seconds)
        ├─ t=7.5: Update session status "generating"
        ├─ t=8.5: Create detailed feedbacks (async DB write)
        └─ t=9.0: Update session status "in_progress"

t=8.0   [PULL PHASE] Worker pulls Job2 from Redis (after rate limit)
        └─→ asyncio.create_task(process_interview_job(Job2))
        └─→ Worker doesn't wait - returns to queue immediately
        └─→ Next allowed pull: t=15.0

        [BACKGROUND TASK] Job2 starts executing (Job1 still running!)
        ├─ t=8.1: RAG query (async, ~2 seconds)
        ├─ t=10.1: LLM generation (async, ~4-6 seconds)
        ├─ t=14.5: Update session status "generating"
        ├─ t=15.5: Create detailed feedbacks (async DB write)
        └─ t=16.0: Update session status "in_progress"

t=9.0   Job1 finishes (concurrent with Job2 running!)
        └─→ Session 1 marked as "in_progress"
        └─→ User1 can now submit answers

t=15.0  [PULL PHASE] Worker pulls Job3 from Redis
        └─→ asyncio.create_task(process_interview_job(Job3))
        └─→ Next allowed pull: t=22.0

        [BACKGROUND TASK] Job3 starts (Job1 done, Job2 still running!)

t=16.0  Job2 finishes
        └─→ Session 2 marked as "in_progress"
        └─→ User2 can now submit answers

t=22.0  [PULL PHASE] Worker pulls Job4 from Redis

...and so on...
```

---

## Key Concurrency Characteristics

### FastAPI Request Handling (Incoming)
- **Concurrency Level**: Unlimited (depends on Uvicorn workers)
- **Pattern**: Each request is handled by an async handler
- **Behavior**: 
  - Multiple requests processed simultaneously
  - HTTP response returned immediately (job queued in Redis)
  - No blocking - requests don't wait for job completion

### Worker Job Processing (Background)
- **Concurrency Level**: Limited by rate limiter (1 job pull every ~7 seconds)
- **Pattern**: Rate-limited pulling + concurrent task execution
- **Behavior**:
  ```python
  while True:
      sleep(rate_limit_gap)              # ← Rate limit enforcement
      job = await redis.pull()            # ← Pull 1 job at a time
      asyncio.create_task(process(job))   # ← Schedule task (NON-BLOCKING!)
      loop_back()                         # ← Immediately get next job
  ```

### Concurrent Task Execution
- **Number of Concurrent Tasks**: Multiple (depends on how many were scheduled before first completes)
- **Example with 7-second rate limit**:
  - If each job takes 8-10 seconds:
    - t=7.0: Pull Job1, schedule it
    - t=8.0: Job1 still running, Pull Job2, schedule it
    - t=9.0: Job1 finishes, Job2 running, Pull Job3, schedule it
    - **Concurrency: 2-3 jobs running simultaneously**

  - If each job takes 20 seconds:
    - t=7.0: Pull Job1, schedule it (will finish at t=27.0)
    - t=14.0: Job1 still running, Pull Job2, schedule it
    - t=21.0: Job1 still running, Job2 still running, Pull Job3
    - **Concurrency: 2-3 jobs running simultaneously**

---

## Database Consistency Model

```
Each Job Execution:

1. await session_service.update_session_status(session_id, "generating")
   └─→ ASYNC DB WRITE (updates immediately)

2. await retrieve_questions_from_rag(cv_text)
   └─→ ASYNC IO (doesn't block other tasks)

3. await generate_interview_questions(...)
   └─→ ASYNC LLM CALL (doesn't block other tasks)

4. await feedback_service.create_detailed_feedbacks_batch(...)
   └─→ ASYNC DB WRITE (batch insert)

5. await session_service.update_session_status(session_id, "in_progress")
   └─→ ASYNC DB WRITE (final update)

All these operations use AsyncClient from Supabase
└─→ DB operations don't block the event loop
└─→ Other tasks can progress while waiting for DB/LLM
```

---

## Scenario: 10 Concurrent Users

```
USER SUBMISSIONS (t=0 to t=0.5 seconds):
User1 → Request received, Job1 queued ✓
User2 → Request received, Job2 queued ✓
User3 → Request received, Job3 queued ✓
...
User10 → Request received, Job10 queued ✓

All 10 users get HTTP 200 responses immediately
└─→ Sessions created with status "queued"

---

WORKER PROCESSING (starts at t=1.0):

t=1.0   Pull Job1 → Schedule task1
t=8.0   Pull Job2 → Schedule task2 (task1 still running!)
t=15.0  Pull Job3 → Schedule task3 (tasks 1,2 still running!)
t=22.0  Pull Job4 → Schedule task4
...

CONCURRENT EXECUTION (all tasks using async/await):
├─ task1: RAG query → LLM call → DB updates (t=1-10s)
├─ task2: RAG query → LLM call → DB updates (t=8-18s)
├─ task3: RAG query → LLM call → DB updates (t=15-25s)
├─ task4: RAG query → LLM call → DB updates (t=22-32s)
└─ ... more tasks

RESULT:
✓ Jobs complete in 8-10 seconds each (not queued)
✓ CPU/IO time efficient (no blocking)
✓ Database doesn't become bottleneck
✓ LLM API calls don't block job queue
✓ Users see "in_progress" within seconds of submission
```

---
