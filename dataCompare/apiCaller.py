from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GROQ_API_KEY')
client = Groq(api_key=api_key)


def llm_caller(prompt):
    # print("Calling LLM with prompt:", prompt)  # Debugging print to see the prompt
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {
                "role": "system",
                "content":
                    "You are an expert in document identity verification. "
                    "Compare two pieces of text to check if they refer to the same entity, "
                    "even with variations in abbreviations, name formats, or title differences. "
                    "example Job in X is same as reserch analyst in X,core member in X is same as head in department of X"
                    "Respond with ONLY one word: '0' for no, '1' for yes. DO NOT provide explanations, thoughts, or additional text."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_completion_tokens=1024, 
        top_p=1,
        stream=False,
        stop=None,
    )
    # print(completion)  # Debugging print to see the full response object
    # Extract the response and clean it up
    original_response = completion.choices[0].message
    # print(original_response)  # Debugging print to see raw output
    response = original_response.content.strip()
    
    # Isolate the last word (should be 0 or 1) or default to "0" if empty
    result = response.split()[-1] if response else "0"
    return result
