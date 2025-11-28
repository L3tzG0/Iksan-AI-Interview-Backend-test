"""
LLM Service - Skeleton Implementation

This service wraps LLM functionality for generating interview questions
based on document content (resume, portfolio, etc.)

IMPLEMENTATION GUIDE FOR FUTURE ASYNC LLM INTEGRATION:
======================================================
When implementing actual LLM calls, use async-friendly HTTP clients:

1. For OpenAI:
   - Use `openai.AsyncOpenAI` client
   - Example:
     ```python
     from openai import AsyncOpenAI
     client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
     response = await client.chat.completions.create(...)
     ```

2. For Google Gemini:
   - Use `google.generativeai` with async support or `httpx.AsyncClient`
   - Example with httpx:
     ```python
     import httpx
     async with httpx.AsyncClient() as client:
         response = await client.post(url, json=payload, headers=headers)
     ```

3. For Anthropic Claude:
   - Use `anthropic.AsyncAnthropic` client
   - Example:
     ```python
     from anthropic import AsyncAnthropic
     client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
     response = await client.messages.create(...)
     ```

IMPORTANT: Do NOT use synchronous HTTP clients (requests, urllib) in async functions.
If you must use a sync client, convert the method to regular `def` and let FastAPI
run it in a thread pool automatically.

Current Status: Skeleton implementation with placeholder data.
"""

from typing import List
from app.core.config import settings


class LLMService:
    """
    Service for LLM-based interview question generation.
    
    This is a skeleton implementation that returns placeholder questions.
    Replace with actual LLM API calls when integrating with a provider.
    
    ASYNC DESIGN DECISION:
    - Currently using sync `def` because this is a placeholder returning static data
    - When implementing actual LLM calls:
      * If using async client (httpx.AsyncClient, openai.AsyncOpenAI): change to `async def`
      * If using sync client (requests): keep as `def` and FastAPI handles threading
    """
    
    def __init__(self):
        """
        Initialize LLM service.
        
        TODO: Add async LLM client initialization here
        Example with OpenAI:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        Example with httpx (for custom API):
            # Client should be created per-request or use connection pooling
            # self.base_url = settings.LLM_API_BASE_URL
        """
        self.model = settings.LLM_MODEL
        self.num_questions = 10
    
    def generate_interview_questions(self, cleaned_text: str) -> List[str]:
        """
        Generate interview questions based on the provided document text.
        
        Args:
            cleaned_text: Cleaned/extracted text from the student's document
                         (resume, portfolio, etc.)
        
        Returns:
            List[str]: List of 10 interview questions
        
        FUTURE ASYNC IMPLEMENTATION:
        ============================
        When implementing with actual LLM, change signature to:
            async def generate_interview_questions(self, cleaned_text: str) -> List[str]:
        
        Example with OpenAI AsyncClient:
        ```python
        async def generate_interview_questions(self, cleaned_text: str) -> List[str]:
            prompt = self._build_prompt(cleaned_text)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE
            )
            return self._parse_questions(response.choices[0].message.content)
        ```
        
        Example with httpx.AsyncClient:
        ```python
        async def generate_interview_questions(self, cleaned_text: str) -> List[str]:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.LLM_API_URL}/generate",
                    json={"text": cleaned_text, "model": self.model},
                    headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                    timeout=30.0
                )
                response.raise_for_status()
                return self._parse_questions(response.json())
        ```
        """
        # Skeleton implementation - returns placeholder questions
        # These will be replaced by actual LLM-generated questions
        placeholder_questions = [
            "자기소개를 해주세요. (Please introduce yourself.)",
            "이 분야에 관심을 갖게 된 계기는 무엇인가요? (What made you interested in this field?)",
            "본인의 강점과 약점은 무엇이라고 생각하시나요? (What do you think are your strengths and weaknesses?)",
            "팀 프로젝트 경험에 대해 말씀해주세요. (Tell me about your team project experience.)",
            "가장 도전적이었던 경험은 무엇인가요? (What was your most challenging experience?)",
            "해당 경험에서 어떤 것을 배우셨나요? (What did you learn from that experience?)",
            "5년 후 자신의 모습을 어떻게 그리고 계신가요? (How do you envision yourself in 5 years?)",
            "스트레스 상황에서 어떻게 대처하시나요? (How do you handle stressful situations?)",
            "왜 이 직무/분야를 선택하셨나요? (Why did you choose this job/field?)",
            "마지막으로 하고 싶은 말씀이 있으신가요? (Is there anything else you would like to say?)",
        ]
        
        return placeholder_questions
    
    def _build_prompt(self, cleaned_text: str) -> str:
        """
        Build the prompt for LLM question generation.
        
        Args:
            cleaned_text: Document text to base questions on
        
        Returns:
            str: Formatted prompt for LLM
        
        TODO: Implement proper prompt engineering based on chosen LLM provider
        """
        # Placeholder prompt template
        prompt = f"""
Based on the following document content, generate 10 interview questions
that would help assess the candidate's qualifications, experiences, and potential.

Document Content:
{cleaned_text}

Generate exactly 10 questions in Korean, focusing on:
1. Personal introduction and motivation
2. Relevant experiences and skills mentioned in the document
3. Problem-solving abilities
4. Future goals and career aspirations
5. Soft skills and teamwork

Return the questions as a numbered list.
"""
        return prompt
    
    def _parse_questions(self, llm_response: str) -> List[str]:
        """
        Parse LLM response to extract questions list.
        
        Args:
            llm_response: Raw text response from LLM
        
        Returns:
            List[str]: Parsed list of questions
        
        TODO: Implement robust parsing logic based on LLM output format
        """
        # Placeholder - implement based on actual LLM response format
        # Example: split by newlines, filter numbered items, clean up
        lines = llm_response.strip().split('\n')
        questions = []
        for line in lines:
            line = line.strip()
            # Remove numbering (e.g., "1.", "1)", "1:")
            if line and line[0].isdigit():
                # Find where the actual question starts
                for i, char in enumerate(line):
                    if char in '.):' and i < 3:
                        line = line[i+1:].strip()
                        break
            if line:
                questions.append(line)
        return questions[:self.num_questions]
