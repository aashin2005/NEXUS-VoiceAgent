from groq import Groq
import json
import random

client = Groq(api_key="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")

def generate_adaptive_question(subject, difficulty, interview_history):
    # Formats the interview history log for the cloud model
    history_context = ""
    for index, turn in enumerate(interview_history):
        history_context += f"\nTurn {index+1}:\nQuestion Asked: {turn['question']}\nCandidate Spoke: {turn['user_answer']}\nAI Assessment Feedback: {turn['feedback']}\n"

    prompt = f"""
    You are a live, elite technical recruiter conducting a precise interview on {subject} ({difficulty} level).
    
    Conversation History Log:
    {history_context if history_context else "No questions asked yet. This is the absolute start of the interview."}
    
    YOUR ASSIGNMENT:
    Read the log above. Act like a real person tracking an applicant:
    - If the candidate answered poorly, ask a precise follow-up question drilling down into that exact structural weakness.
    - If they answered perfectly, step up the complexity of the next system concept.
    - NEVER ask a question or concept that has been mentioned in the log history above.
    
    You must return a JSON block with exactly two keys: "q" (the next question string) and "a" (the expected benchmark answer string).
    """

    try:
        # Requesting Groq's lightning-fast cloud open-source engine
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}  # Absolutely guarantees pure raw JSON output
        )
        
        raw_text = response.choices[0].message.content.strip()
        return json.loads(raw_text)
        
    except Exception as e:
        print(f"!!! Groq Cloud Error Fallback: {e}")
        # Safeguard fallback dictionary pool so your UI screen never freezes
        backup_pool = [
            {"q": f"Can you explain the core execution architecture patterns under the hood of {subject}?", "a": "How variables, tasks, and memory compilation states execute at runtime."},
            {"q": f"What is a common error or memory performance block developers face in {subject}, and how do you solve it?", "a": "Handling execution stack leaks, scope binding issues, or invalid reference management."}
        ]
        return random.choice(backup_pool)