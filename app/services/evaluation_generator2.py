import os
import json
import time
import httpx
import asyncio
import math
from typing import Dict, Any, List
from pydantic import BaseModel

# NOTE: Importing core models from the existing schema file
from app.schemas.interview_session import (
    QuestionAnswerPair, 
    DetailedEvaluationItem,
    OverallScores,
    SessionSummary,
    NextStepItem,
)
from app.core.config import settings

# --- Internal LLM Output Wrapper (Required for service validation and return type) ---
class EvaluationBatchResponse(BaseModel):
    """The single, comprehensive JSON object returned by the service, combining LLM output and backend calculation."""
    per_question_feedback: List[DetailedEvaluationItem] 
    overall_scores: OverallScores # Calculated by the backend
    session_summary: SessionSummary
    next_steps: List[NextStepItem] 


# --- Configuration ---
MODEL_NAME = "gemini-2.5-flash"
API_URL_TEMPLATE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key="
API_KEY = settings.GEMINI_API_KEY

# --- Detailed System Prompt and Rubric (FINAL ADJUSTMENTS) ---
SYSTEM_PROMPT = """
You are a highly analytical, unbiased interview evaluation engine. Your sole task is to assess a candidate's interview session against a precise BARS (Behaviorally Anchored Rating Scale) scoring rubric and provide comprehensive structured feedback.

INPUT: A list of N question and answer pairs (where N is between 1 and 10), including the quantitative speech metrics for each answer. These metrics (WPM, Silence Ratio, PPM) have been pre-calculated from the raw audio duration, word count, and pause data.
OUTPUT: A single JSON object containing per-question scores/feedback, overall summaries, and next step recommendations.

#################### SCORING RUBRIC (BARS - 4 DIMENSIONS) ####################

All scores MUST be a float between 0.0 and 10.0.

1. CONTENT RELEVANCE (CR) - Measures how well the core answer matches the question's intent, **including the professionalism and tone of the delivery**.
    - Score 0-3: The answer completely misses the point, contains major inaccuracies, or is nonsensical. Tone is highly unprofessional or negative.
    - Score 4-6: The answer is generally related but lacks depth, contains minor inaccuracies, or addresses only a small part of the question. Tone is acceptable but lacks enthusiasm or polish.
    - Score 7-10: The answer is highly accurate, directly addresses all components of the question, demonstrates deep knowledge, and is delivered with a clear, professional, and enthusiastic tone.

2. STRUCTURE (ST) - Measures clarity and coherence using the STAR method proxy, **including vocabulary choice and grammatical correctness**.
    - Score 0-3: Rambling, disorganized, or abrupt; grammar/vocabulary is poor, severely damaging clarity.
    - Score 4-6: Partial structure (e.g., provides Situation and Action, but misses Task or Result). Grammar is adequate but includes noticeable errors or weak vocabulary.
    - Score 7-10: Clear, compelling narrative (STAR or logical flow) supported by sophisticated and correct grammar/vocabulary.

3. FLUENCY & SPEED (FL) - Measures speech flow, pace, and conversational ease (simulated via transcript and quantitative metrics).
    - USE METRIC: Words Per Minute (WPM) and Silence Ratio.
    - Score 0-3: Very slow pace (e.g., < 80 WPM) or a high silence ratio (> 25%).
    - Score 4-6: Acceptable pace (e.g., 80-120 WPM) but still some non-verbal hesitation and notable pauses (15-25% silence).
    - Score 7-10: Smooth, conversational pace (e.g., 120-180 WPM), minimal filler words, and a low silence ratio (< 15%).

4. CONFIDENCE PROXY (CP) - Measures consistency and self-assurance (simulated speech rate stability and pause frequency).
    - USE METRIC: Pauses Per Minute (PPM).
    - Score 0-5: The answer has a very high frequency of pauses (e.g., > 10 PPM), suggesting inconsistency or anxiety.
    - Score 6-10: The answer shows a low frequency of pauses (e.g., < 8 PPM), indicating a controlled, measured, and consistent pace, conveying competence and self-assurance.

#################### OUTPUT REQUIREMENTS ####################

1. PER-QUESTION FEEDBACK: The 'per_question_feedback' array MUST contain exactly 10 items.
    - For the N completed questions, provide CR, ST, FL, and CP scores (0.0 to 10.0) and a concise 'evaluation_text'. The evaluation_text MUST include feedback on grammar, vocabulary, also speed and professional tone when applicable.
    - For any remaining questions (from N up to 9, where N < 10), you MUST insert a placeholder object at the end of the array with the following values:
        - cr_score, st_score, fl_score, cp_score: 0.0
        - evaluation_text: "Question not answered by the candidate."
        - is_correct: false
        - overall_score: 0.0
2. SESSION SUMMARY: Provide separate 2-3 sentence summaries for 'strength_text' and 'areas_for_growth_text'. The analysis MUST be holistic, referencing patterns across ONLY the N COMPLETED QUESTIONS.
3. NEXT STEPS: Provide EXACTLY 3 actionable 'NextStepItem' recommendations, based ONLY on the N COMPLETED QUESTIONS.
"""

def _get_pydantic_properties(model: BaseModel) -> Dict[str, Any]:
    """Helper to extract properties and required fields from a Pydantic model for inline use."""
    # Use by_alias=True to ensure we use cr_score, st_score, etc., in the API schema
    schema = model.model_json_schema(by_alias=True)
    
    # The API expects properties to be defined directly without external definitions.
    return {
        "type": "OBJECT",
        "properties": schema.get('properties', {}),
        "required": schema.get('required', [])
    }


def get_evaluation_generation_schema() -> Dict[str, Any]:
    """
    Manually constructs the comprehensive JSON response schema for the LLM, 
    using the core models from the interview_session schema.
    """
    
    # 1. Get inline schemas for all nested components
    detailed_item_schema = _get_pydantic_properties(DetailedEvaluationItem)
    session_summary_schema = _get_pydantic_properties(SessionSummary)
    next_step_item_schema = _get_pydantic_properties(NextStepItem)

    # 2. Construct the final, compliant response schema using inline definitions
    schema_definition = {
        "type": "OBJECT",
        "properties": {
            "per_question_feedback": {
                "type": "ARRAY",
                "description": "A list containing exactly 10 detailed feedback objects, padded with placeholders if N < 10.",
                "items": detailed_item_schema
            },
            # overall_scores removed here, will be calculated later
            "session_summary": session_summary_schema,
            "next_steps": {
                "type": "ARRAY",
                "description": "Exactly 3 actionable next step recommendations.",
                "items": next_step_item_schema
            }
        },
        # Ensure the top-level required fields match the expected response (excluding overall_scores for AI output)
        "required": ["per_question_feedback", "session_summary", "next_steps"]
    }
    
    return schema_definition


def _calculate_overall_scores(feedback_items: List[DetailedEvaluationItem]) -> OverallScores:
    """Calculates the overall averages across all completed questions."""
    
    # Filter out placeholder items (overall_score 0.0 implies unanswered)
    completed_items = [item for item in feedback_items if item.overall_score > 0.0]
    
    if not completed_items:
        return OverallScores(
            content_relevance_score=0.0,
            structure_score=0.0,
            fluency_score=0.0,
            confidence_proxy_score=0.0,
            overall_score=0.0
        )
        
    num_completed = len(completed_items)
    
    # Use the long-form field names for summation (populated via Pydantic aliases)
    cr_sum = sum(item.content_relevance_score for item in completed_items)
    st_sum = sum(item.structure_score for item in completed_items)
    fl_sum = sum(item.fluency_score for item in completed_items)
    cp_sum = sum(item.confidence_score for item in completed_items)
    
    # Calculate averages for each dimension
    cr_avg = round(cr_sum / num_completed, 2)
    st_avg = round(st_sum / num_completed, 2)
    fl_avg = round(fl_sum / num_completed, 2)
    cp_avg = round(cp_sum / num_completed, 2)
    
    # Calculate the overall score (average of the 4 dimension averages)
    # Note: Using 10.0 scale, not 100
    overall_score_final = round((cr_avg + st_avg + fl_avg + cp_avg) / 4.0, 2)

    return OverallScores(
        content_relevance_score=cr_avg,
        structure_score=st_avg,
        fluency_score=fl_avg,
        confidence_proxy_score=cp_avg,
        overall_score=overall_score_final
    )


async def generate_session_evaluation(qa_pairs: List[QuestionAnswerPair]) -> EvaluationBatchResponse:
    """
    Calls the Gemini API to generate structured evaluation.
    Calculates fluency/speed metrics and calculates the overall_scores in the backend.
    """
    if not API_KEY:
        raise Exception("API Key is missing. Ensure settings.GEMINI_API_KEY is configured.")
    
    # --- Metric Calculation (Remains the same) ---
    qa_text = "\n\n--- INTERVIEW TRANSCRIPT AND METRICS ---\n"
    
    for qa in qa_pairs:
        total_pause_duration_seconds = qa.total_pause_duration_seconds
        total_pause_count = qa.total_pause_count

        word_count = qa.word_count
        audio_duration = qa.audio_duration_seconds
        # Calculate time spent speaking
        speaking_time_seconds = audio_duration - total_pause_duration_seconds
        
        # Handle edge cases where metrics are zero or invalid
        if audio_duration == 0 or speaking_time_seconds <= 0 or word_count == 0:
            wpm = 0.0
            silence_ratio = 100.0 if audio_duration > 0 else 0.0
            ppm = 0.0
        else:
            wpm = (word_count / speaking_time_seconds) * 60.0
            silence_ratio = (total_pause_duration_seconds / audio_duration) * 100.0
            ppm = (total_pause_count / audio_duration) * 60.0
            
        metrics_string = (
            f"| METRICS | WPM: {wpm:.1f} | Silence Ratio: {silence_ratio:.1f}% | PPM: {ppm:.1f} |\n"
            f"| RAW DATA | Audio Duration: {audio_duration:.1f}s | Word Count: {word_count} | Pauses: {total_pause_count} | Pause Duration: {total_pause_duration_seconds:.1f}s |\n"
        )
        
        qa_text += f"Q{qa.question_order}: {qa.question_text}\n"
        qa_text += f"A{qa.question_order} (Transcript): {qa.answer_text}\n"
        qa_text += metrics_string
        qa_text += "\n"
        
    num_completed_questions = len(qa_pairs)
    num_unanswered_questions = 10 - num_completed_questions
    
    qa_text += "--------------------------------------\n\n"
    
    user_query = (
        f"Based on the following {num_completed_questions} Q&A pair(s) (out of 10 total), "
        f"and strictly using the quantitative metrics provided for FLUENCY and CONFIDENCE PROXY scoring, "
        f"provide the full structured JSON evaluation. "
        f"Remember to evaluate only the {num_completed_questions} answers provided. "
        f"Then, you MUST add {num_unanswered_questions} placeholder item(s) to the end of the 'per_question_feedback' array, "
        f"using the original question order and placeholder values for unanswered questions, to ensure its length is exactly 10.\n\n"
        f"{qa_text}"
    )
    
    response_schema = get_evaluation_generation_schema()

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
            "temperature": 0.5 
        },
    }

    headers = {'Content-Type': 'application/json'}
    api_url = API_URL_TEMPLATE + API_KEY 
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status() 
            
            result = response.json()
            
            candidate = result.get('candidates', [{}])[0]
            json_text = candidate.get('content', {}).get('parts', [{}])[0].get('text')
            
            if not json_text:
                raise ValueError("Gemini returned empty or malformed text response.")
            
            if json_text.strip().startswith('```') and json_text.strip().endswith('```'):
                json_text = json_text.strip().strip('`').lstrip('json').strip()

            parsed_json = json.loads(json_text)
            
            # --- POST-PROCESSING: Calculate and Inject Overall Scores ---
            
            # 1. Parse the per-question feedback into Pydantic models for easy calculation
            feedback_items_raw = parsed_json.get("per_question_feedback", [])
            # Note: We must use the model_dump(by_alias=False) from the LLM response 
            # for correct score field mapping when creating the DetailedEvaluationItem objects.
            feedback_items = [DetailedEvaluationItem(**item) for item in feedback_items_raw] 
            
            # 2. Calculate the overall score object
            overall_scores_obj = _calculate_overall_scores(feedback_items)

            # 3. Add the calculated overall scores back to the parsed JSON
            # Use model_dump(by_alias=False) to ensure the keys match the final schema (e.g., content_relevance_score)
            parsed_json['overall_scores'] = overall_scores_obj.model_dump(by_alias=False)
            
            # 4. Validate the *complete* response against the EvaluationBatchResponse model
            validated_response = EvaluationBatchResponse(**parsed_json)
            
            return validated_response

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError, json.JSONDecodeError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
            else:
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 400:
                    print(f"\n--- FATAL 400 ERROR DETAIL ---")
                    print(e.response.text) # Print the full API error detail
                    print("------------------------------\n")
                raise Exception(f"Failed to generate evaluation after {max_retries} attempts. Last Error: {e}")