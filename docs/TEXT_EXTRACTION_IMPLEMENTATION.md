# Text Extraction Implementation


### Extraction Methods

- **PDF**: PyMuPDF (fitz) - Fast, lightweight extraction
- **DOCX**: python-docx - Paragraphs + tables extraction
- **TXT**: PyMuPDF - UTF-8 decoding with fallback
- **MD**: PyMuPDF - Preserves markdown structure

### Text Cleaning (LLM-Optimized)

- Single-pass whitespace normalization
- Multiple spaces -> Single space
- Excessive newlines -> Max 2 consecutive
- Control character removal (keeps newline/tab)
- Unicode normalization (NFKC)

### Performance

- **PDF (1-5 pages)**: 50-200ms extraction + 1-5ms cleaning
- **DOCX (Resume)**: 20-100ms extraction + 1-3ms cleaning  
- **TXT/MD**: 5-20ms extraction + <1ms cleaning
- **Total**: 25ms - 1s for typical documents


## Database Schema Update

The `documents` table now stores:

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    raw_text TEXT,        -- Unmodified extraction
    cleaned_text TEXT,    -- LLM-optimized version
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Flow

```
1. POST /api/v1/sessions/initiate
   ↓
2. File upload (PDF/DOCX/TXT/MD) OR raw_text
   ↓
3. File validation (type, signature, size)
   ↓
4. Text extraction -> (raw_text, cleaned_text)
   ↓
5. Store both versions in documents table
   ↓
6. Return session response
```

## Security

- File type validation (MIME type)
- File signature verification (magic numbers)
- File size limits (10MB default)
- Empty file detection
- Corrupted file handling


### Libraries Used

- **PyMuPDF (fitz)** - v1.26.6+ - PDF/TXT/MD extraction
- **python-docx** - v1.21.0+ - DOCX extraction
- **Standard library** - re, unicodedata, io, typing, logging

### Optimizations

- No external API calls
- Simple string operations
- Fast libraries - C-based implementations  

### Error Handling

- Empty file validation
- File size validation  
- Unsupported type detection

##  Notes

- **No chunking implemented** - To be added later if needed for large documents
- **Token counting** - Can be added using tiktoken library if required
- **DOCX tables** - Extract and preserve tables in output
