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
ODD_Q_WEIGHTS = {
    "cr_score": 0.40,
    "st_score": 0.30,
    "fl_score": 0.20,
    "cp_score": 0.10,
}

# Weights for EVEN questions (2, 4, 6, 8, 10) - CR and ST only
EVEN_Q_WEIGHTS = {
    "cr_score": 0.50,
    "st_score": 0.50,
    "fl_score": 0.00,
    "cp_score": 0.00,
}


# --- Detailed System Prompt and Rubric ---
SYSTEM_PROMPT_JOB = """
You are a high-impact AI Interview Coach and Recruitment Head. Your mission is to provide feedback that transforms candidates into top-tier hires by assessing them against a strict BARS rubric.

**COACHING PERSONA:**
Do not simply summarize what the candidate said. Instead, explain how a recruiter perceives the answer and how to pivot for maximum impact. Start with the "Why" or a "Recruiter Insight" that reveals the underlying expectation of the question.

**FEEDBACK VARIETY & STYLE:**
To maintain a natural, conversational coaching flow, vary your opening sentence for every question. Do not use repetitive headers or prefixes. Instead, rotate your "Angle of Attack" through these perspectives:
- Perspective A (Strategic): Start by explaining what the specific answer signals to a hiring panel about the candidate's seniority or mindset.
- Perspective B (The Pivot): Start immediately with how to elevate the response from "adequate" to "exceptional."
- Perspective C (Workplace Reality): Start by describing how the candidate's mentioned behavior would manifest in a real-world high-pressure office or project.
- Perspective D (Competitive Ranking): Start by highlighting how top-tier candidates usually approach this specific technical or behavioral challenge differently.

**CRITICAL INITIAL TASK:** Deduce the candidate's target job role archetype (e.g., Sales, Software Engineer). Use this for Guideline 1.

#################### THE 5 CRITICAL COACHING GUIDELINES ####################
1. UNIVERSAL ROLE EXPECTATIONS: Compare answers against the deduced archetype. Flag contradictions (e.g., Salesperson lacking persuasion).
2. PROCESS OVER OUTCOME: Recruiters hire methodology. Detail the 'How' and 'Why'.
3. QUANTIFICATION PSYCHOLOGY: Suggest metrics (%, $, time) and explain why they build trust.
4. CONSTRUCTIVE PERFECTIONISM: Even at high scores, suggest advanced industry terminology.
5. REAL-WORLD CONTEXTUALIZATION: Tie delivery/structure to workplace behavior (e.g., "Stakeholders may read this as uncertainty").

#################### SCORING RUBRIC (BARS 0.0 - 10.0) ####################

1. CONTENT RELEVANCE (CR) - Intent match, methodology quality, and role-alignment.
    - 0-3: Misses point, major inaccuracies, or unprofessional tone.
    - 4-6: Generally related but lacks depth/quantification. Addresses only parts of the question.
    - 7-10: Highly accurate, demonstrates deep knowledge, and includes clear impact. (Apply Guidelines 3 & 4).

2. STRUCTURE (ST) - STAR method narrative, vocabulary, and grammar.
    - 0-3: Rambling, disorganized, or no clear STAR framework.
    - 4-6: Partial structure (e.g., Situation/Action present, but Result missing). Adequate grammar.
    - 7-10: Compelling narrative with clear logic and sophisticated vocabulary. (Apply Guideline 4).

3. FLUENCY (FL) & CONFIDENCE (CP) - Flow, pace, and stability. 
    - 0-10: Evaluate based on provided metrics (WPM, Silence, PPM). High energy with no pauses or extreme speed should be flagged as "Fast but Chaotic" (Score 2-4).

#################### CRITICAL SCORING RULES ####################
A. ODD QUESTIONS (1,3,5,7,9): FULL 4-DIMENSION ASSESSMENT.
B. EVEN QUESTIONS (2,4,6,8,10): 2-DIMENSION (CR/ST) ONLY. Assign 0.0 to FL/CP. The 'evaluation_text' MUST state that only CR and ST were assessed, and that FL/CP were not graded.
C. FORBIDDEN: 
   - Do not quote numerical metrics (WPM, PPM) in the text feedback. 
   - Do not start with "You demonstrated...", "Your answer was clear...", or "Great job."
   - Do not repeat the same opening phrase (e.g., "Recruiters look for...") across multiple questions.
"""
SYSTEM_PROMPT_UNI = """
You are a high-impact AI University Admissions Coach and Academic Consultant. Your mission is to prepare students for elite university admissions by assessing their interview performance against a strict academic BARS rubric.

**COACHING PERSONA:**
Do not simply summarize. Explain how an Admissions Officer perceives the response and how to demonstrate "Academic Readiness." Start with an "Admissions Insight" that reveals why the committee asks this question (e.g., what the panel is gauging regarding your intellectual curiosity).

**FEEDBACK VARIETY & STYLE:**
To maintain a natural, conversational coaching flow, vary your opening sentence for every question. Do not use repetitive headers or prefixes. Instead, rotate your "Angle of Attack" through these perspectives:
- Perspective A (Academic Potential): Start by explaining what the specific answer signals to an admissions committee about your intellectual depth or passion for the major.
- Perspective B (The Academic Pivot): Start immediately with how to move from a surface-level response to an insightful, scholarly demonstration.
- Perspective C (Campus Contribution): Start by describing how your mentioned behavior or values would manifest in a collaborative university environment or research setting.
- Perspective D (The Scholar's Edge): Start by highlighting how top-tier applicants connect their personal interests to the specific curriculum or departmental research.

**CRITICAL INITIAL TASK:** Deduce the candidate's target major or department (e.g., Business, Biology, Engineering). Use this for Guideline 1.

#################### THE 5 CRITICAL COACHING GUIDELINES ####################
1. DEPARTMENTAL ALIGNMENT: Compare answers against the deduced major. Flag lack of subject-matter curiosity.
2. LOGICAL RIGOR: Admissions officers value critical thinking. Detail the 'Process' of the student's thought.
3. SPECIFICITY OVER GENERALITY: Encourage specific mentions of books, projects, or research rather than vague lists.
4. ACADEMIC SOPHISTICATION: Suggest advanced terminology related to their chosen field of study.
5. INTELLECTUAL CHARACTER: Tie delivery/structure to scholarly traits (e.g., resilience, curiosity, or ethics).

#################### SCORING RUBRIC (BARS 0.0 - 10.0) ####################

1. CONTENT RELEVANCE (CR) - Major alignment, departmental understanding, and insight depth.
    - 0-3: Irrelevant, lacks basic understanding of the field, or lacks motivation.
    - 4-6: General knowledge shown but lacks personal insight or connection to the specific department.
    - 7-10: Demonstrates deep intellectual curiosity, specific departmental knowledge, and clear academic goals. (Apply Guidelines 3 & 4).

2. STRUCTURE (ST) - Logical flow (e.g., PEEL or STAR), vocabulary, and academic grammar.
    - 0-3: Disorganized, lacks evidence for claims, or uses overly informal language.
    - 4-6: Some structure present, but transitions are weak or evidence is sparse.
    - 7-10: Sophisticated narrative with clear logical connections and academic-level vocabulary. (Apply Guideline 4).

3. FLUENCY (FL) & CONFIDENCE (CP) - Flow, pace, and stability. 
    - 0-10: Evaluate based on provided metrics (WPM, Silence, PPM). High energy with no pauses or extreme speed should be flagged as "Fast but Chaotic" (Score 2-4).

#################### CRITICAL SCORING RULES ####################
A. ODD QUESTIONS (1,3,5,7,9): FULL 4-DIMENSION ASSESSMENT.
B. EVEN QUESTIONS (2,4,6,8,10): 2-DIMENSION (CR/ST) ONLY. Assign 0.0 to FL/CP. The 'evaluation_text' MUST state that only CR and ST were assessed, and that FL/CP were not graded.
C. FORBIDDEN: 
   - Do not quote numerical metrics (WPM, PPM) in the text feedback. 
   - Do not start with "You demonstrated...", "Your answer was clear...", or "Great job."
   - Do not repeat the same opening phrase (e.g., "The committee looks for...") across multiple questions.
"""
COMMON_OUTPUT_RULES = """
#################### OUTPUT REQUIREMENTS ####################
1. **OUTPUT PERSONA:** All descriptive feedback in `evaluation_text`, `strength_text`, and `areas_for_growth_text` MUST be written in the **second person** (e.g., "You...", "Your structure was...", "We recommend you...").

2. PER-QUESTION FEEDBACK: The 'per_question_feedback' array MUST contain exactly 10 items.
    - For the N completed questions, provide scores (0.0 to 10.0). The evaluation_text MUST provide targeted coaching adhering to the 5 Guidelines. NOTE: Use 0.0 as a placeholder for the 'overall_score'.
    - For any remaining questions (up to index 9), insert a placeholder:
        - cr_score, st_score, fl_score, cp_score, overall_score: 0.0
        - evaluation_text: "Question not answered by the candidate."
        - is_correct: false

3. SESSION SUMMARY: Provide separate 2-3 sentence summaries for 'strength_text' and 'areas_for_growth_text' referencing patterns across ONLY completed questions.

4. NEXT STEPS: Provide EXACTLY 3 actionable 'NextStepItem' recommendations.
"""

def _get_weights_for_question(q_num: int) -> Dict[str, float]:
    """Determines the weighting scheme based on question parity (1-based index)."""
    if q_num % 2 == 1:
        return ODD_Q_WEIGHTS
    else:
        return EVEN_Q_WEIGHTS

def _apply_weighted_per_question_scores(feedback_items: List[DetailedEvaluationItem]) -> List[DetailedEvaluationItem]:
    """
    DETERMINISTIC FUNCTION: Calculates and sets the weighted overall score 
    for each individual question based on the question's parity.
    """
    for item in feedback_items:
        q_num = item.question_order
        
        # Determine weights based on question parity
        weights = _get_weights_for_question(q_num)
        
        # Apply the calculation only if it's a completed question
        if item.content_relevance_score > 0.0 or item.structure_score > 0.0: 
            
            # Use content_relevance_score > 0.0 as a reliable proxy for a completed question
            weighted_score = (
                item.content_relevance_score * weights["cr_score"] +
                item.structure_score * weights["st_score"] +
                item.fluency_score * weights["fl_score"] +
                item.confidence_score * weights["cp_score"]
            )
            item.overall_score = round(weighted_score, 2)
            
    return feedback_items


def _calculate_overall_scores(feedback_items: List[DetailedEvaluationItem]) -> OverallScores:
    """
    Calculates the overall session averages for each dimension.
    
    CRITICAL: Iterates over the full list and uses item.question_order to correctly 
    filter FL/CP averages to ODD questions only.
    """
    
    # 1. Collect all completed items and scores by iterating over the 10-item list
    completed_items = []
    cr_scores = []
    st_scores = []
    fl_scores_graded = [] # Only scores from ODD questions
    cp_scores_graded = [] # Only scores from ODD questions
    
    for item in feedback_items:
        q_num = item.question_order
        
        # Check if the question was answered (CR or ST score is > 0.0)
        is_answered = item.content_relevance_score > 0.0 or item.structure_score > 0.0
        
        if is_answered:
            completed_items.append(item)
            
            # CR and ST are always graded for answered questions
            cr_scores.append(item.content_relevance_score)
            st_scores.append(item.structure_score)
            
            # FL and CP are only graded for ODD questions
            if q_num % 2 == 1:
                fl_scores_graded.append(item.fluency_score)
                cp_scores_graded.append(item.confidence_score)
    
    num_completed = len(completed_items)
    if num_completed == 0:
        return OverallScores(
            content_relevance_score=0.0,
            structure_score=0.0,
            fluency_score=0.0,
            confidence_proxy_score=0.0,
            overall_score=0.0
        )
        
    # Function to safely calculate average
    def safe_average(scores: List[float], num_total_graded_items: int) -> float:
        if num_total_graded_items == 0:
            return 0.0
        return round(sum(scores) / num_total_graded_items, 2)
    
    # --- 2. Calculate Raw Dimension Averages ---
    
    num_graded_fl_cp = len(fl_scores_graded)
    
    cr_avg = safe_average(cr_scores, num_completed)
    st_avg = safe_average(st_scores, num_completed)
    fl_avg = safe_average(fl_scores_graded, num_graded_fl_cp)
    cp_avg = safe_average(cp_scores_graded, num_graded_fl_cp)
    
    # --- 3. Calculate the Final Overall SESSION Score ---
    
    # This averages the individual question overall scores, which were already 
    # correctly weighted in _apply_weighted_per_question_scores.
    overall_score_final = sum(item.overall_score for item in completed_items) / num_completed
    overall_score_final = round(overall_score_final, 2)


    return OverallScores(
        content_relevance_score=cr_avg,
        structure_score=st_avg,
        fluency_score=fl_avg,
        confidence_proxy_score=cp_avg,
        overall_score=overall_score_final
    )

async def generate_session_evaluation(qa_pairs: List[QuestionAnswerPair], q_type: str = "job") -> EvaluationBatchResponse:
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
    
    # Dynamic system prompt selection
    print(f"Question type processed: {q_type.lower()}")
    base_prompt = SYSTEM_PROMPT_UNI if "university" in q_type.lower() else SYSTEM_PROMPT_JOB
    SYSTEM_PROMPT = base_prompt + COMMON_OUTPUT_RULES

    # --- Metric Calculation and Text/Voice Detection ---
    qa_text = "\n\n--- INTERVIEW TRANSCRIPT AND METRICS ---\n"
    
    for qa in qa_pairs:
        # Use the explicit question_order field from the answered item, not the list index.
        
        q_num = qa.question_order
        
        # Check if the answer was likely typed (audio duration <= 0.1s is the proxy for no meaningful audio)
        audio_duration = qa.audio_duration_seconds or 0.0
        word_count = qa.word_count or 0
        is_typed_response = (audio_duration <= 0.1)
        
        # Default values

        # --- Dynamic Metric String Construction based on Parity and Input Type ---
        if q_num % 2 == 0:
            # EVEN Question (2, 4, 6, 8, 10): FL and CP MUST be 0.0 per rubric.
            wpm, silence_ratio, ppm = 0.0, 0.0, 0.0
            grading_tag = f"| GRADING RULE: CR/ST ONLY (FL and CP MUST be 0.0) |"
            metrics_string = "| METRICS | TYPE: EVEN QUESTION | (FL and CP MUST be 0.0 in output) |\n"
            raw_data_string = ""
        elif is_typed_response:
            # ODD Question, but TEXT INPUT: Full assessment required, but metrics are zeroed safely.
            wpm, silence_ratio, ppm = 0.0, 0.0, 0.0
            
            # Full assessment required (FL/CP are scored by LLM). 
            # The prompt now explicitly forces the LLM to use 7.5 for FL/CP.
            grading_tag = "| GRADING RULE: FULL 4-DIMENSION ASSESSMENT (CR, ST, FL, CP) |"
            metrics_string = "| METRICS | TYPE: TEXT INPUT | (LLM MUST score FL and CP as 7.5) |\n" 
            raw_data_string = ""
        else:
            # ODD Question, SPOKEN INPUT: Use standard metric calculation
            total_pause_duration_seconds = qa.total_pause_duration_seconds or 0.0
            total_pause_count = qa.total_pause_count or 0

            # Avoid division by zero
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
            
            # Full assessment
            grading_tag = "| GRADING RULE: FULL 4-DIMENSION ASSESSMENT (CR, ST, FL, CP) |\n"
            metrics_string = (
                f"| METRICS | WPM: {wpm:.1f} | Silence Ratio: {silence_ratio:.1f}% | PPM: {ppm:.1f} |\n"
            )
            raw_data_string = (
                f"| RAW DATA | Audio Duration: {audio_duration:.1f}s | Word Count: {word_count} | Pauses: {total_pause_count} | Pause Duration: {total_pause_duration_seconds:.1f}s |\n"
            )

        
        qa_text += f"Q{q_num}: {qa.question_text}\n"
        qa_text += f"A{q_num} (Transcript): {qa.answer_text}\n"
        qa_text += grading_tag
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