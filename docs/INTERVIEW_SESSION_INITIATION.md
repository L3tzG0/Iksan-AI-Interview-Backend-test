# Interview Session Initiation - Documentation

## Overview

The interview session initiation process allows students to upload documents (resume, portfolio, etc.) to start a new AI interview session. The system processes the document text extraction synchronously and stores it for interview generation.

**Note:** File storage to Supabase bucket is currently **deprecated**. Files are processed in-memory only, and text content is stored in the database.

## Architecture

### Flow Diagram

```
Frontend → Upload Document → Backend API
                                ↓
                        Validate File Type & Size
                                ↓
                    Create Session (status: "in_progress")
                                ↓
                    Extract Text from Document (in-memory)
                                ↓
                    Save raw_text to documents table
                                ↓
                Create detailed_feedbacks record (session_id only)
                                ↓
                    Return Success Response
                                ↓
            (If any step fails → Mark session as "failed")
```

---

**Last Updated:** November 26, 2025  
**API Version:** v1  
**Status:** Development (Storage deprecated, text extraction placeholder)
