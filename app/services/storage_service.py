import uuid
import re
from datetime import datetime
from typing import Optional
from pathlib import Path
from fastapi import HTTPException, UploadFile
from supabase import AsyncClient
from app.core.config import settings


class StorageService:
    """
    Service for handling Supabase storage operations
    
    DEPRECATED: Storage functionality is currently not in use.
    This service is preserved for future implementation when file storage is needed.
    Currently only used for file validation (validate_file method).
    """
    
    # File signatures (magic numbers) for allowed file types
    FILE_SIGNATURES = {
        'application/pdf': [b'%PDF'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [b'PK\x03\x04'],  # ZIP-based format
        'text/plain': [],  # Text files don't have specific signatures
        'text/markdown': []  # Markdown files don't have specific signatures
    }
    
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
    
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
    
    def _generate_storage_path(
        self, 
        student_id: int, 
        session_id: int, 
        filename: str
    ) -> str:
        """
        Generate unique storage path for document
        
        Format: interviews/{student_id}/{session_id}/{uuid}_{filename}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = filename.replace(" ", "_")
        
        return f"interviews/{student_id}/{session_id}/{timestamp}_{unique_id}_{safe_filename}"
    
    async def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        student_id: int,
        session_id: int
    ) -> str:
        """
        Upload document to Supabase storage
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            content_type: MIME type
            student_id: Student ID
            session_id: Session ID
        
        Returns:
            str: Storage path of uploaded file
        
        Raises:
            HTTPException: If upload fails
        """
        # Check file size
        if len(file_bytes) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Generate storage path
        storage_path = self._generate_storage_path(student_id, session_id, filename)
        
        try:
            # Upload to Supabase storage
            response = self.supabase.storage.from_(self.bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type}
            )
            
            return storage_path
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to storage: {str(e)}"
            )
    
    async def delete_document(self, path: str) -> bool:
        """
        Delete document from storage
        
        Args:
            path: Storage path of file to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.supabase.storage.from_(self.bucket).remove([path])
            return True
        except Exception as e:
            # Log error but don't raise - this is cleanup operation
            print(f"Warning: Failed to delete file from storage: {str(e)}")
            return False
    
    async def get_public_url(self, path: str) -> str:
        """
        Get public URL for a document
        
        Args:
            path: Storage path
        
        Returns:
            str: Public URL
        """
        try:
            response = await self.supabase.storage.from_(self.bucket).get_public_url(path)
            return response
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get public URL: {str(e)}"
            )
