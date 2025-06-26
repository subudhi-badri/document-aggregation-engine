# ==============================================================================
#  dataCompare/main.py - FINAL VERSION USING DIRECT GOOGLE GEMINI API
# ==============================================================================

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import backoff
from google.api_core import exceptions as google_exceptions

# --- Load Environment Variables ---
load_dotenv()

# --- Direct Google AI Client Configuration ---
# Ensure your GOOGLE_API_KEY is set in your .env file
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please check your .env file.")
genai.configure(api_key=GOOGLE_API_KEY)

# This decorator will catch the specific "429 Resource Exhausted" error from Google
# and retry with an exponential backoff.
@backoff.on_exception(
    backoff.expo,
    google_exceptions.ResourceExhausted, # The specific exception for 429 errors
    max_tries=4
)
def compare_multi_source_data(all_data):
    """
    Takes a dictionary with resume and multiple sources and asks the direct
    Google Gemini API to perform a highly detailed, structured comparison.
    """
    data_str = json.dumps(all_data, indent=2)

    # ============================================================================ #
    # === FINAL, UPGRADED PROMPT WITH SCORE & DISCREPANCY TYPES ================== #
    # ============================================================================ #
    prompt_template = """
    You are a meticulous HR compliance analyst and data forensic expert. Your task is to conduct a deep comparison of a candidate's profile, aggregated from multiple sources.

    Here is the aggregated data:
    --- AGGREGATED JSON DATA ---
    {json_data_placeholder}
    --- END AGGREGATED JSON DATA ---

    **Your Task:**
    Return ONLY a single, valid JSON object that IS the final report. It must strictly adhere to this structure:
    `{{ "consistency_score": <number>, "overall_summary": "...", "key_highlights": [], "discrepancies": [] }}`.

    **1. Consistency Score (`consistency_score`):**
    - You MUST provide a numerical score from 0 (completely different) to 100 (perfectly identical) representing the overall alignment between all provided sources.

    **2. Overall Summary (`overall_summary`):**
    - Provide a concise paragraph summarizing the candidate's profile and the consistency level, referencing the score.

    **3. Key Highlights (`key_highlights`):**
    - This should be a list summarizing the most important information from each platform.
    - You MUST create ONLY ONE entry per source (e.g., one for 'GitHub', one for 'LinkedIn', one for 'Resume').
    - For each source, summarize its key contributions in a comprehensive 'highlight' string. Use bullet points within the string (e.g., \\n- ) if there are multiple points.
    - **If a source provides no significant information or was not available (e.g., contains an 'error' field), you MUST explicitly state that in the highlight string.**
    
    - Example of a good entry:
      ```json
      {
        "source": "GitHub",
        "highlight": "- Demonstrates active coding skills with 5 recent repositories.\n- Contributed to the open-source project 'data-validator'."
      }
      ```
      ```json
      {
        "source": "LeetCode",
        "highlight": "Has a strong competitive programming profile with 250+ problems solved, including 50 hard problems."
      }
      ```
      ```json
      {
        "source": "Kaggle",
        "highlight": "Achieved 'Contributor' tier, indicating participation in data science competitions."
      }
      ```
    - Example for a missing source:
      ```json
      {
        "source": "Google Scholar",
        "highlight": "No Google Scholar profile was found or provided."
      }
      ```

    **4. Detailed Discrepancies (`discrepancies`):**
    - For each discrepancy, use this exact format:
      `{"type": "...", "field": "...", "details": "...", "notes": "..."}`
    
    - ### CRITICAL RULE FOR THIS SECTION ###
    - **Every single item in the 'discrepancies' list MUST be a complete JSON object with all four keys: 'type', 'field', 'details', and 'notes'.**
    - **DO NOT include simple strings or incomplete objects in the list.**
    
    - **`type`**: You MUST categorize each discrepancy as one of the following strings: "Direct Contradiction", "Data Omission", or "Vague vs. Specific". This field is mandatory.
    - **`field`**: The data field being compared (e.g., "Experience at TechCorp", "Contact Phone").
    - **`details`**: A string summarizing the different values, e.g., "Resume: 'Software Engineer' vs. LinkedIn: 'Senior Software Engineer'".
    - **`notes`**: Your brief analysis of the discrepancy's potential significance.
    - If NO meaningful discrepancies are found, return an EMPTY LIST `[]`.
    """

    comparison_prompt = prompt_template.replace('{json_data_placeholder}', data_str)

    # Configure the model for JSON output
    generation_config = {
        "response_mime_type": "application/json",
    }
    
    # Select the Gemini model
    model = genai.GenerativeModel(
        "gemini-1.5-flash-latest",
        generation_config=generation_config
    )

    try:
        print("[*] Calling Google Gemini API for final analysis with scoring...")
        response = model.generate_content(comparison_prompt)
        ai_response_str = response.text
        print("[✓] Received scored comparison report from Google AI.")
        return ai_response_str
    except Exception as e:
        print(f"[!] An error occurred while calling the Google Gemini API for comparison: {e}")
        return None

# The old 'compare_json_data' function is no longer needed and has been removed.