import logging
import re
import unicodedata
from typing import Tuple
from io import BytesIO

logger = logging.getLogger(__name__)


class TextExtractionService:
    """Service for extracting text from various document formats optimized for LLM consumption"""
    
    def extract_text_from_file(self, file_bytes: bytes, content_type: str) -> Tuple[str, str]:
        """
        Extract text from file bytes based on content type and return both raw and cleaned versions
        
        Args:
            file_bytes: File content as bytes
            content_type: MIME type of file
        
        Returns:
            Tuple[str, str]: (raw_text, cleaned_text) where cleaned_text is optimized for LLM
        
        Raises:
            ValueError: If file is invalid or extraction fails
        """
        # Validate input
        if not file_bytes:
            raise ValueError("File is empty")
        
        if len(file_bytes) < 10:
            raise ValueError("File too small to contain valid content")
        
        logger.info(f"Extracting text from {content_type}, size: {len(file_bytes)} bytes")
        
        try:
            # Route to appropriate extraction method
            if content_type == "application/pdf":
                raw_text = self._extract_from_pdf(file_bytes)
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                raw_text = self._extract_from_docx(file_bytes)
            elif content_type in ["text/plain", "text/markdown"]:
                raw_text = self._extract_from_text(file_bytes)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Validate extraction result
            if not raw_text or len(raw_text.strip()) < 5:
                logger.warning(f"Extraction produced minimal text: {len(raw_text)} chars")
            
            # Clean text for LLM consumption
            cleaned_text = self._clean_text_for_llm(raw_text)
            
            logger.info(f"Extraction successful - Raw: {len(raw_text)} chars, Cleaned: {len(cleaned_text)} chars")
            
            return raw_text, cleaned_text
            
        except Exception as e:
            logger.error(f"Text extraction failed for {content_type}: {str(e)}")
            raise ValueError(f"Failed to extract text: {str(e)}")
    
    def _extract_from_pdf(self, file_bytes: bytes) -> str:
        """
        Extract text from PDF file using PyMuPDF (fitz)
        Optimized for speed using simple text extraction
        
        Args:
            file_bytes: PDF file content as bytes
        
        Returns:
            str: Extracted text from all pages
        
        Raises:
            ValueError: If PDF extraction fails
        """
        try:
            import fitz  # PyMuPDF
            
            # Open PDF from bytes
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            # Extract text from all pages (fast list comprehension)
            text_parts = [page.get_text() for page in doc]
            
            # Close document
            doc.close()
            
            # Join with double newline as page separator
            return "\n\n".join(text_parts)
            
        except ImportError:
            logger.error("PyMuPDF (fitz) not installed")
            raise ValueError("PDF extraction library not available")
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def _extract_from_docx(self, file_bytes: bytes) -> str:
        """
        Extract text from DOCX file using python-docx
        Includes paragraphs and tables for complete content extraction
        
        Args:
            file_bytes: DOCX file content as bytes
        
        Returns:
            str: Extracted text from document
        
        Raises:
            ValueError: If DOCX extraction fails
        """
        try:
            from docx import Document
            
            # Open DOCX from bytes
            doc = Document(BytesIO(file_bytes))
            
            # Extract paragraphs (filter empty ones)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            # Extract tables (important for resumes/CVs)
            table_texts = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        table_texts.append(row_text)
            
            # Combine all text
            all_text = paragraphs + table_texts
            return "\n".join(all_text)
            
        except ImportError:
            logger.error("python-docx not installed")
            raise ValueError("DOCX extraction library not available")
        except Exception as e:
            logger.error(f"DOCX extraction error: {str(e)}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    def _extract_from_text(self, file_bytes: bytes) -> str:
        """
        Extract text from plain text or markdown file
        Can use PyMuPDF for consistent handling or simple decode
        
        Args:
            file_bytes: Text file content as bytes
        
        Returns:
            str: Decoded text content
        
        Raises:
            ValueError: If text extraction fails
        """
        try:
            # Try PyMuPDF first for consistency (handles various text encodings)
            import fitz  # PyMuPDF
            
            doc = fitz.open(stream=file_bytes, filetype="txt")
            text = doc[0].get_text()  # Text files are single-page documents
            doc.close()
            
            return text
            
        except Exception as e:
            # Fallback to direct UTF-8 decoding
            logger.warning(f"PyMuPDF text extraction failed, using fallback: {str(e)}")
            try:
                return file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Try with error handling
                return file_bytes.decode('utf-8', errors='replace')
    
    def _clean_text_for_llm(self, text: str) -> str:
        """
        Fast, lightweight text cleaning for LLM consumption
        Optimized for speed with minimal operations
        
        Operations:
        1. Normalize whitespace (single regex pass)
        2. Remove control characters
        3. Normalize unicode
        
        Args:
            text: Raw extracted text
        
        Returns:
            str: Cleaned text ready for LLM
        """
        if not text:
            return ""
        
        # 1. Normalize spacing - replace multiple spaces/tabs with single space
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 2. Normalize newlines - max 2 consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 3. Remove control characters except newline and tab
        text = ''.join(c for c in text if c.isprintable() or c in '\n\t')
        
        # 4. Unicode normalization (NFKC - compatibility composition)
        # Handles edge cases like ligatures, superscripts, etc.
        text = unicodedata.normalize('NFKC', text)
        
        # 5. Strip leading/trailing whitespace
        return text.strip()
