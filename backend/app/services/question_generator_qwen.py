# import json
# import logging
# from typing import List, Optional
# from openai import AsyncOpenAI
# import httpx

# from app.schemas.interview_session import GeneratedQuestion
# from app.core.config import settings
# from pydantic import BaseModel

# # --- Setup Logging ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - QWEN_GEN - %(message)s')

# # --- Internal LLM Output Wrapper ---
# class QuestionGenerationResponse(BaseModel):
#     """The structure expected from the Qwen API."""
#     questions: List[GeneratedQuestion]

# # --- Configuration ---
# MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"

# # --- Deferred Client Initialization ---
# global_qwen_client = None

# SYSTEM_PROMPT = """
# You are a highly analytical and experienced HR Manager conducting a preliminary interview screening. 
# Your task is to generate exactly 10 structured interview questions for the candidate based on their provided CV/introduction text, 
# specifically focusing on the target role and field provided.

# RULES FOR QUESTION GENERATION:
# 1. Total Questions: Exactly 10 questions.
# 2. Structure: 
#     - Questions 1-5 MUST be general, behavioral, or soft-skill based.
#     - Questions 6-10 MUST be a deep dive into the candidate's specific experience/resume.
# 3. Flow: Questions must flow naturally, starting broad (Q1-5) and moving to detailed technical probes (Q6-10).
# 4. Output: The response MUST be a single, valid JSON object. Do not include any conversational text before or after the JSON.
# """

# async def generate_interview_questions_qwen(
#         cv_text: str,
#         field: str,
#         role: str,
#         reference_questions: Optional[List[str]] = None
# ) -> List[GeneratedQuestion]:
#     """
#     Calls the Qwen API (OpenAI-compatible) to generate structured interview questions.
#     """
#     global global_qwen_client 
    
#     if global_qwen_client is None:
#         try:
#             global_qwen_client = AsyncOpenAI(
#                 api_key=settings.QWEN_API_KEY,
#                 base_url=f"http://{settings.QWEN_API_BASE_URL}/v1",
#                 timeout=httpx.Timeout(120.0, connect=10.0)
#             )
#             logging.info("Qwen Async Client successfully initialized.")
#         except Exception as e:
#             logging.error(f"FATAL: Could not initialize Qwen client: {e}")
#             raise Exception("Qwen API Client initialization failed.")

#     rag_context_text = ""
#     if reference_questions:
#         rag_context_joined = "\n- ".join(reference_questions)
#         rag_context_text = f"REFERENCE QUESTIONS (Use for style guidance): - {rag_context_joined}"
    
#     user_query = (
#         f"Generate the 10 questions for a '{role}' role in the '{field}' industry. "
#         f"Context:\n\n---\n{cv_text}\n---\n{rag_context_text}\n\n"
#         f"Return ONLY a JSON object with a 'questions' array containing 10 objects with 'question_text' and 'question_order'."
#     )

#     try:
#         response = await global_qwen_client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": user_query}
#             ],
#             temperature=0.7,
#             response_format={"type": "json_object"} # If supported by your backend
#         )

#         content = response.choices[0].message.content.strip()
        
#         # Simple JSON extraction in case of markdown blocks
#         if "```json" in content:
#             content = content.split("```json")[1].split("```")[0].strip()
#         elif "```" in content:
#             content = content.split("```")[1].split("```")[0].strip()

#         parsed_json = json.loads(content)
#         validated_response = QuestionGenerationResponse(**parsed_json)
            
#         return validated_response.questions

#     except Exception as e:
#         logging.error(f"Qwen Generation Error: {e}")
#         raise Exception(f"Qwen failed to generate questions: {e}")