import re
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.core.config import settings


class StorageService:
    """
    Service for handling file validation and storage operations.
    
    Currently only used for file validation (validate_file, verify_file_signature).
    Storage functionality can be implemented when needed with any backend.
    """
    
    # File signatures (magic numbers) for allowed file types
    FILE_SIGNATURES = {
        'application/pdf': [b'%PDF'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [b'PK\x03\x04'],  # ZIP-based format
        'text/plain': [],  # Text files don't have specific signatures
    }
    
    def __init__(self, db=None):
        """Initialize StorageService. The db parameter is kept for API compatibility but not used."""
        pass
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks
        
        Args:
            filename: Original filename
        
        Returns:
            str: Sanitized filename
        
        Raises:
            HTTPException: If filename is invalid or dangerous
        """
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Filename cannot be empty"
            )
        
        # Get just the filename without path components
        filename = Path(filename).name
        
        # Remove or replace dangerous characters
        # Allow only alphanumeric, dots, hyphens, underscores
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Prevent hidden files
        if sanitized.startswith('.'):
            sanitized = 'file' + sanitized
        
        # Prevent empty filename after sanitization
        if not sanitized or sanitized == '.':
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )
        
        # Limit filename length
        max_length = 255
        if len(sanitized) > max_length:
            name_part = sanitized[:max_length - 40]  # Leave room for extension and UUID
            ext_part = Path(sanitized).suffix
            sanitized = name_part + ext_part
        
        return sanitized
    
    def verify_file_signature(self, file_bytes: bytes, content_type: str) -> bool:
        """
        Verify file signature (magic numbers) matches the declared content type
        
        Args:
            file_bytes: File content as bytes
            content_type: Declared MIME type
        
        Returns:
            bool: True if signature matches or no signature check needed
        
        Raises:
            HTTPException: If signature doesn't match declared type
        """
        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        signatures = self.FILE_SIGNATURES.get(content_type, [])
        
        # If no signatures defined (e.g., text files), skip check
        if not signatures:
            return True
        
        # Check if file starts with any of the valid signatures
        for signature in signatures:
            if file_bytes.startswith(signature):
                return True
        
        raise HTTPException(
            status_code=400,
            detail=f"File content does not match declared type: {content_type}"
        )
    
    def validate_file(self, file: UploadFile) -> None:
        """
        Validate file type and size
        
        Raises:
            HTTPException: If file is invalid
        """
        # Check content type
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # Sanitize filename
        if file.filename:
            try:
                self.sanitize_filename(file.filename)
            except HTTPException:
                raise
        
        # Note: file.size might not be available for all UploadFile instances
        # We'll check size after reading the bytes
