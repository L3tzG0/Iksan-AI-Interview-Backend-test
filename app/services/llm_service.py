"""
LLM Service - Skeleton Implementation

This service wraps LLM functionality for generating interview questions
based on document content (resume, portfolio, etc.)

TODO: Replace placeholder implementation with actual LLM integration
(e.g., OpenAI, Anthropic, Google AI, etc.)
"""

from typing import List
from app.core.config import settings


class LLMService:
    """
    Service for LLM-based interview question generation.
    
    This is a skeleton implementation that returns placeholder questions.
    Replace with actual LLM API calls when integrating with a provider.
    """
    
    def __init__(self):
        """
        Initialize LLM service.
        
        TODO: Add LLM client initialization here
        Example:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        """
        self.model = settings.LLM_MODEL
        self.num_questions = 10
    
    async def generate_interview_questions(self, cleaned_text: str) -> List[str]:
        """
        Generate interview questions based on the provided document text.
        
        Args:
            cleaned_text: Cleaned/extracted text from the student's document
                         (resume, portfolio, etc.)
        
        Returns:
            List[str]: List of 10 interview questions
        
        TODO: Implement actual LLM call
        Example implementation:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Document: {cleaned_text}"}
                ]
            )
            return parse_questions(response.choices[0].message.content)
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
    
    async def _build_prompt(self, cleaned_text: str) -> str:
        """
        Build the prompt for LLM question generation.
        
        Args:
            cleaned_text: Document text to base questions on
        
        Returns:
            str: Formatted prompt for LLM
        
        TODO: Implement proper prompt engineering
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
