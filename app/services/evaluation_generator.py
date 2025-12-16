import json
from typing import Dict, Any, List
import logging
from pydantic import BaseModel, ValidationError

# New SDK Imports
from google import genai
from google.genai import types
from google.genai.errors import APIError

# NOTE: Importing core models from the existing schema file
from app.schemas.interview_session import (
    QuestionAnswerPair, 
    DetailedEvaluationItem,
    OverallScores,
    SessionSummary,
    NextStepItem,
)
from app.core.config import settings

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - EVAL_GEN - %(message)s')

# --- Internal LLM Output Wrapper (LLM is instructed *not* to calculate overall_scores) ---
class EvaluationLLMOutput(BaseModel):
    """The JSON object structure that the LLM is explicitly asked to return."""
    per_question_feedback: List[DetailedEvaluationItem] 
    session_summary: SessionSummary
    next_steps: List[NextStepItem] 

# --- Final Return Type (Includes Python-calculated scores) ---
class EvaluationBatchResponse(BaseModel):
    """The single, comprehensive JSON object returned by the service, combining LLM output and backend calculation."""
    per_question_feedback: List[DetailedEvaluationItem] 
    overall_scores: OverallScores 
    session_summary: SessionSummary
    next_steps: List[NextStepItem] 


# --- Configuration ---
MODEL_NAME = "gemini-2.5-flash"

# --- Deferred Client Initialization ---
global_client = None

# --- SCORING WEIGHTS (Used by Python code for all overall score calculations) ---
# Weights must sum to 1.0 (100%).
SCORING_WEIGHTS = {
    "cr_score": 0.40,
    "st_score": 0.30,
    "fl_score": 0.20,
    "cp_score": 0.10,
}


# --- Detailed System Prompt and Rubric ---
SYSTEM_PROMPT = """
You are a highly experienced and professional AI interview coach and **Recruitment Specialist**. Your sole task is to assess an interview session against a precise BARS (Behaviorally Anchored Rating Scale) scoring rubric and provide comprehensive, structured, and **DIRECT second-person feedback.**

**CRITICAL INITIAL TASK:** Based on the content and nature of the questions and answers provided, you MUST first deduce the candidate's target job role archetype (e.g., Sales, Software Engineer, Accountant, Project Manager). Use this deduction for Guideline 1.

INPUT: A list of N question and answer pairs (where N is between 1 and 10), including the quantitative speech metrics for each answer.
OUTPUT: A single JSON object containing per-question scores/feedback, overall summaries, and next step recommendations.

#################### CRITICAL GUIDELINES FROM RECRUITMENT EXPERTS ####################
You MUST strictly adhere to these 5 professional feedback guidelines in your evaluation:

1. UNIVERSAL ROLE EXPECTATIONS (CRITICAL): Compare the answer against the general archetype of the deduced job role. For example, a Sales professional must show negotiation/persuasion; an Accountant must demonstrate ethics/accuracy. If the answer contradicts the core traits of this role archetype (e.g., an Accountant talking about creative design), **flag the mismatch in Content Relevance (CR) feedback.**

2. PROCESS OVER OUTCOME (CRITICAL): Recruiters hire on methodology. Do not just praise the result (the "What"). **CR feedback MUST detail the quality of the step-by-step approach, diagnostic steps, or technical logic (the "How" and "Why").** If the process is missing, the feedback must demand a systematic, structured approach.

3. QUANTIFICATION PSYCHOLOGY: If the answer lacks quantifiable results, the feedback MUST proactively suggest specific metrics (e.g., time, money saved, percentages, frequency). When numbers ARE used, the feedback MUST explain the business value (e.g., "This quantification builds trust and helps the interviewer calculate ROI.").

4. CONSTRUCTIVE PERFECTIONISM (CRITICAL): **You MUST ensure there is always room to grow.** Even if a score of 10.0 is assigned, the feedback MUST include a suggestion for upgrading vocabulary to advanced, industry-specific terminology (e.g., changing "checking mistakes" to "implementing Quality Assurance protocol"). **Never give a "Perfect, nothing to add" response.**

5. REAL-WORLD CONTEXTUALIZATION: Always relate the feedback to a simulated workplace behavior. Tie delivery issues (pace, tone) or structural weaknesses directly to a professional scenario (e.g., "This speed might make a client feel rushed," or "This disorganized structure is inappropriate for a stakeholder report").

#################### SCORING RUBRIC (BARS - 4 DIMENSIONS) ####################

All scores MUST be a float between 0.0 and 10.0.
Your task is only to provide the four component scores (CR, ST, FL, CP) and the evaluation text. The final overall score will be calculated by the backend system.

1. CONTENT RELEVANCE (CR) - Measures how well the core answer matches the question's intent, **the quality of the technical/methodological process demonstrated (Guideline 2),** and the answer's alignment with the deduced job role archetype **(Guideline 1).**
    - Score 0-3: Your answer completely misses the point, contains major inaccuracies, or is nonsensical. Your tone is highly unprofessional or negative.
    - Score 4-6: Your answer is generally related but lacks depth, contains minor inaccuracies, or addresses only a small part of the question. Your tone is acceptable but lacks enthusiasm or polish.
    - Score 7-10: Your answer is highly accurate, directly addresses all components of the question, demonstrates deep knowledge, and is delivered with a clear, professional, and enthusiastic tone. **The evaluation_text MUST fulfill Guideline 3 (Quantification) and Guideline 4 (Perfectionism).**

2. STRUCTURE (ST) - Measures clarity and coherence using the STAR method proxy, **including vocabulary choice and grammatical correctness.**
    - Score 0-3: Your response is rambling, disorganized, or abrupt; grammar/vocabulary is poor, severely damaging clarity.
    - Score 4-6: Your response uses partial structure (e.g., provides Situation and Action, but misses Task or Result). Your grammar is adequate but includes noticeable errors or weak vocabulary.
    - Score 7-10: Your response demonstrates a clear, compelling narrative (STAR or logical flow) supported by sophisticated and correct grammar/vocabulary. **The evaluation_text MUST fulfill Guideline 4 (Perfectionism).**

3. FLUENCY & SPEED (FL) - Measures speech flow, pace, and conversational ease (simulated via transcript and quantitative metrics). **Feedback MUST apply Guideline 5 (Real-World Context).**
    - **CRITICAL USE OF METRIC:** You MUST analyze the WPM and Silence Ratio metrics to score FL, but the **evaluation_text MUST NOT quote the numerical values.** Express the result qualitatively (e.g., "Your pace was smooth," or "Your silence ratio was too high").
    - Score 0-3: Very slow pace or a high silence ratio. Fluency is severely impaired by hesitations.
    - Score 4-6: Acceptable pace but still some non-verbal hesitation and notable pauses.
    - Score 7-10: Smooth, conversational pace, minimal filler words, and a low silence ratio.

4. CONFIDENCE PROXY (CP) - Measures consistency and self-assurance (simulated speech rate stability and pause frequency). **Feedback MUST apply Guideline 5 (Real-World Context).**
    - **CRITICAL USE OF METRIC:** You MUST analyze the PPM metric to score CP, but the **evaluation_text MUST NOT quote the numerical PPM value.** Express the result qualitatively (e.g., "Your pacing was controlled," or "The high frequency of pauses indicated anxiety").
    - Score 0-5: Your answer has a very high frequency of pauses, suggesting inconsistency or anxiety.
    - Score 6-10: Your answer shows a low frequency of pauses, indicating a controlled, measured, and consistent pace, conveying competence and self-assurance.

#################### CRITICAL SCORING RULE: TEXT INPUT ####################
IF the transcript input section contains the tag **| TYPE: TEXT INPUT |**, it means speech metrics are unavailable. In this case:
1. You MUST assign FL (Fluency) and CP (Confidence Proxy) scores of **7.5** (neutral score).
2. The 'evaluation_text' for that question MUST explicitly state that FL and CP were scored neutrally because the answer was typed, and focus all feedback only on CR and ST.
############################################################################


#################### OUTPUT REQUIREMENTS ####################

1. **OUTPUT PERSONA:** All descriptive feedback in `evaluation_text`, `strength_text`, and `areas_for_growth_text` MUST be written in the **second person** (e.g., "You demonstrated...", "Your structure was...", "We recommend you practice...").
2. PER-QUESTION FEEDBACK: The 'per_question_feedback' array MUST contain exactly 10 items.
    - For the N completed questions, provide CR, ST, FL, and CP scores (0.0 to 10.0). The evaluation_text MUST provide targeted feedback on all scored dimensions, and **adhere to the 5 Critical Guidelines above, without quoting numerical metrics.** **NOTE: For these completed questions, use 0.0 as a placeholder for the 'overall_score'.**
    - For any remaining questions (from N up to 9, where N < 10), you MUST insert a placeholder object at the end of the array with the following values:
        - cr_score, st_score, fl_score, cp_score, overall_score: 0.0
        - evaluation_text: "Question not answered by the candidate."
        - is_correct: false
    
3. SESSION SUMMARY: Provide separate 2-3 sentence summaries for 'strength_text' and 'areas_for_growth_text'. The analysis MUST be holistic, referencing patterns across ONLY the N COMPLETED QUESTIONS.
4. NEXT STEPS: Provide EXACTLY 3 actionable 'NextStepItem' recommendations, based ONLY on the N COMPLETED QUESTIONS.
"""

def _apply_weighted_per_question_scores(feedback_items: List[DetailedEvaluationItem]) -> List[DetailedEvaluationItem]:
    """
    DETERMINISTIC FUNCTION: Calculates and sets the weighted overall score 
    for each individual question based on SCORING_WEIGHTS.
    """
    for item in feedback_items:
        # Use content_relevance_score > 0.0 as a reliable proxy for a completed question
        if item.content_relevance_score > 0.0 or item.structure_score > 0.0: 
            
            weighted_score = (
                item.content_relevance_score * SCORING_WEIGHTS["cr_score"] +
                item.structure_score * SCORING_WEIGHTS["st_score"] +
                item.fluency_score * SCORING_WEIGHTS["fl_score"] +
                item.confidence_score * SCORING_WEIGHTS["cp_score"]
            )
            item.overall_score = round(weighted_score, 2)
            
    return feedback_items


def _calculate_overall_scores(feedback_items: List[DetailedEvaluationItem]) -> OverallScores:
    """
    Calculates the overall session averages for each dimension, and then 
    calculates the final overall session score using the SCORING_WEIGHTS.
    """
    
    # Filter out placeholder items 
    completed_items = [item for item in feedback_items if item.content_relevance_score > 0.0]
    
    if not completed_items:
        return OverallScores(
            content_relevance_score=0.0,
            structure_score=0.0,
            fluency_score=0.0,
            confidence_proxy_score=0.0,
            overall_score=0.0
        )
        
    num_completed = len(completed_items)
    
    # 1. Sum and Average the Dimension Scores across all completed questions
    cr_sum = sum(item.content_relevance_score for item in completed_items)
    st_sum = sum(item.structure_score for item in completed_items)
    fl_sum = sum(item.fluency_score for item in completed_items)
    cp_sum = sum(item.confidence_score for item in completed_items) 
    
    cr_avg = round(cr_sum / num_completed, 2)
    st_avg = round(st_sum / num_completed, 2)
    fl_avg = round(fl_sum / num_completed, 2)
    cp_avg = round(cp_sum / num_completed, 2)
    
    # 2. Calculate the overall SESSION score using the same SCORING_WEIGHTS
    overall_score_final = (
        cr_avg * SCORING_WEIGHTS["cr_score"] +
        st_avg * SCORING_WEIGHTS["st_score"] +
        fl_avg * SCORING_WEIGHTS["fl_score"] +
        cp_avg * SCORING_WEIGHTS["cp_score"]
    )
    overall_score_final = round(overall_score_final, 2)


    return OverallScores(
        content_relevance_score=cr_avg,
        structure_score=st_avg,
        fluency_score=fl_avg,
        confidence_proxy_score=cp_avg,
        overall_score=overall_score_final
    )


async def generate_session_evaluation(qa_pairs: List[QuestionAnswerPair]) -> EvaluationBatchResponse:
    """
    Calls the Gemini API to generate structured evaluation using the native async SDK.
    Applies custom weighted scoring in the backend, and calculates the session overall scores.
    """
    global global_client 
    
    # 1. Initialize the Native Async Client lazily (on first call)
    if global_client is None:
        try:
            # Initialize the synchronous Client, then access the async interface via .aio
            sync_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            global_client = sync_client.aio
            logging.info("Gemini Native Async Client (.aio) successfully initialized for evaluation.")
        except Exception as e:
            logging.error(f"FATAL: Could not initialize Gemini client: {e}")
            raise Exception("Gemini API Client initialization failed.")

    if global_client is None:
         raise Exception("Gemini API Client failed to initialize after attempt.")
    
    # --- Metric Calculation and Text/Voice Detection ---
    qa_text = "\n\n--- INTERVIEW TRANSCRIPT AND METRICS ---\n"
    
    for qa in qa_pairs:
        # Check if the answer was likely typed (word count > 0 but no audio duration)
        is_typed_response = (qa.audio_duration_seconds <= 0.1)
        
        if is_typed_response:
            # Signal to the LLM that this is a text input and metrics are irrelevant
            wpm = 0.0
            silence_ratio = 0.0
            ppm = 0.0
            metrics_string = "| METRICS | TYPE: TEXT INPUT | (FL and CP will be scored 10.0 per rule) |\n"
            raw_data_string = ""
        else:
            # Standard metric calculation for spoken responses
            total_pause_duration_seconds = qa.total_pause_duration_seconds
            total_pause_count = qa.total_pause_count

            word_count = qa.word_count
            audio_duration = qa.audio_duration_seconds
            
            # Avoid division by zero, especially when total speaking time might be zero
            speaking_time_seconds = audio_duration - total_pause_duration_seconds
            speaking_time_seconds = max(speaking_time_seconds, 0.001) # Small epsilon

            if word_count == 0:
                 wpm = 0.0
                 silence_ratio = 100.0 if audio_duration > 0 else 0.0
                 ppm = 0.0
            else:
                 wpm = (word_count / speaking_time_seconds) * 60.0
                 silence_ratio = (total_pause_duration_seconds / audio_duration) * 100.0 if audio_duration > 0 else 0.0
                 ppm = (total_pause_count / audio_duration) * 60.0 if audio_duration > 0 else 0.0
            
            metrics_string = (
                f"| METRICS | WPM: {wpm:.1f} | Silence Ratio: {silence_ratio:.1f}% | PPM: {ppm:.1f} |\n"
            )
            raw_data_string = (
                 f"| RAW DATA | Audio Duration: {audio_duration:.1f}s | Word Count: {word_count} | Pauses: {total_pause_count} | Pause Duration: {total_pause_duration_seconds:.1f}s |\n"
            )
        
        qa_text += f"Q{qa.question_order}: {qa.question_text}\n"
        qa_text += f"A{qa.question_order} (Transcript): {qa.answer_text}\n"
        qa_text += metrics_string
        qa_text += raw_data_string
        qa_text += "\n"
        
    num_completed_questions = len(qa_pairs)
    num_unanswered_questions = 10 - num_completed_questions
    
    qa_text += "--------------------------------------\n\n"
    
    user_query = (
        f"Based on the following {num_completed_questions} Q&A pair(s) (out of 10 total), "
        f"and strictly using the quantitative metrics provided for FLUENCY and CONFIDENCE PROXY scoring, "
        f"and adhering to the CRITICAL SCORING RULE for TEXT INPUT where applicable, "
        f"provide the full structured JSON evaluation. "
        f"The evaluation_text in the response **MUST NOT** quote the specific numerical values of WPM, Silence Ratio, or PPM. "
        f"Remember to evaluate only the {num_completed_questions} answers provided. "
        f"Then, you MUST add {num_unanswered_questions} placeholder item(s) to the end of the 'per_question_feedback' array, "
        f"using the original question order and placeholder values for unanswered questions, to ensure its length is exactly 10.\n\n"
        f"{qa_text}"
    )
    
    # 2. Define the generation configuration using SDK types
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        # Pass the LLM output model class directly for schema definition
        response_schema=EvaluationLLMOutput, 
        temperature=0.5 
    )

    try:
        # 3. Make the single, native asynchronous API call.
        response = await global_client.models.generate_content(
            model=MODEL_NAME,
            contents=[user_query], 
            config=config
        )

        # 4. Response Parsing and Validation
        
        if not response.text:
            raise ValueError("Gemini returned an empty text response.")

        json_text = response.text.strip()
        
        # Clean up potential markdown code block surrounding the JSON
        if json_text.strip().startswith('```') and json_text.strip().endswith('```'):
            json_text = json_text.strip().strip('`').lstrip('json').strip()

        parsed_json = json.loads(json_text)
        
        # Validate LLM output against the LLM-specific model
        validated_llm_output = EvaluationLLMOutput(**parsed_json)
        
        # 5. POST-PROCESSING (Python Backend Calculations)
        
        # A. Parse the LLM's feedback into Pydantic models
        feedback_items = validated_llm_output.per_question_feedback
        
        # B. CRUCIAL STEP: Overwrite the per-question overall_score with the weighted average
        feedback_items = _apply_weighted_per_question_scores(feedback_items)
        
        # C. Calculate the overall session score object 
        overall_scores_obj = _calculate_overall_scores(feedback_items)

        # 6. Reconstruct the Final Response Model
        
        return EvaluationBatchResponse(
            per_question_feedback=feedback_items,
            overall_scores=overall_scores_obj,
            session_summary=validated_llm_output.session_summary,
            next_steps=validated_llm_output.next_steps
        )

    except APIError as e:
        # Catches persistent API errors (400, 429, etc.) after internal retries fail.
        logging.error(f"Gemini API Error (after retries): {e}")
        if hasattr(e, 'response') and e.response is not None:
             logging.error(f"Full response detail: {e.response.text}") 
        raise Exception(f"Failed to generate evaluation due to persistent API error: {e}")
    except (ValueError, json.JSONDecodeError, TypeError, ValidationError) as e:
        # Catches JSON parsing or Pydantic validation errors
        logging.error(f"Failed to parse AI response into structured JSON: {e}")
        raise Exception(f"Failed to generate evaluation due to response parsing error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise Exception(f"An unexpected error occurred during generation: {e}")