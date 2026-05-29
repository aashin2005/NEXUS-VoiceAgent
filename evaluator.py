# evaluator.py

from groq import Groq
import json

client = Groq(api_key="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")

def evaluate_answer(question, user_answer, correct_answer):
    # Quick defense against empty strings or gibberish inputs
    if not user_answer or len(user_answer.strip()) < 5:
        return {
            "score": 0,
            "feedback": "No substantial speech or input was recorded. Please try answering with more technical depth.",
            "status": "Needs Improvement"
        }

    prompt = f"""
    You are an expert technical interviewer evaluating an engineering candidate's response.
    
    Question asked: {question}
    Expected baseline concept: {correct_answer}
    Candidate's answer: {user_answer}
    
    YOUR ASSIGNMENT:
    1. Evaluate the candidate's answer strictly against the expected concept.
    2. Assign an integer score from 0 to 10 (where 0 means entirely incorrect/gibberish, and 10 means flawless professional execution).
    3. Provide a concise, direct 2-sentence feedback review rating their engineering understanding.
    4. Determine the performance status: if the score is 6 or higher, it is "Passed", otherwise it is "Needs Improvement".
    
    You must return a JSON block with exactly three keys: 
    "score" (integer), "feedback" (string), and "status" (string).
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}  # Strictly enforces cloud engine to output JSON
        )
        
        raw_text = response.choices[0].message.content.strip()
        return json.loads(raw_text)
        
    except Exception as e:
        print(f"!!! Cloud Evaluator Error: {e}")
        # Secure fallback schema object so your program loop never breaks
        return {
            "score": 0,
            "feedback": "Your answer was securely processed, but the cloud evaluation failed to return feedback text details.",
            "status": "Needs Improvement"
        }