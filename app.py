from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import io
from datetime import datetime
from groq import Groq
from gtts import gTTS  # ✅ Super stable, 100% free Google engine

# Import your newly created external evaluator module
from evaluator import evaluate_answer

app = Flask(__name__)

# ================= GROQ API SETUP ================= #
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.3-70b-versatile"

# ================= DATA FILE SETUP ================= #
INTERVIEW_FILE = "interviews.json"
QUESTION_FILE = "asked_questions.json"

# Bulletproof structural initializer
for file_path in [INTERVIEW_FILE, QUESTION_FILE]:
    # If file doesn't exist, or is completely empty/blank, write a valid JSON array
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([], f)

# ================= HELPER FUNCTIONS TO PREVENT CORRUPTION ================= #
def load_json_safely(file_path):
    """Safely reads a JSON list file, recovering automatically if corrupted or empty."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        # Auto-recovery: If file has corrupted extra data, fallback to empty array
        print(f"⚠️ Warning: {file_path} had data corruption. Recovering file...")
        return []

def save_json_safely(file_path, data_list):
    """Safely overwrites a file with clean, structured JSON tracking formatting rules."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=4)
    except Exception as e:
        print(f"❌ Failed writing data matrix to {file_path}: {e}")

# ================= PAGES / VIEWS ROUTERS ================= #

@app.route('/')
def home():
    """Renders the Portal Selection Landing Hub"""
    return render_template("home.html")

@app.route('/student', methods=['GET', 'POST'])
def student():
    """Handles the configuration form details before starting"""
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        
        # .strip().upper() forces values into standard casing clean strings
        level = request.form['level'].strip().upper()
        num_questions = request.form['num_questions']

        # 🎯 ALIGNED PERFECTLY WITH YOUR HTML TERMINOLOGY ("ADVANCED" & "BEGINNER")
        if "ADVANCED" in level or "EXPERT" in level:
            behavior_rules = """
            - Persona: Elite, uncompromising Principal Enterprise Architect conducting a high-stakes system design panel.
            - Question Style: Brutal, deep scenario-based engineering challenges. Force the candidate to reason through core runtime compilation mechanics, optimization under tight resource constraints, concurrency/race conditions, system scaling, security vulnerabilities, or deep memory management architecture.
            - Example Format: "Analyze the runtime execution stack under high load. If thousands of sessions invoke function X simultaneously, explain how memory allocation behaves under the hood, identify potential compilation leaks, and detail a complete optimization architecture to mitigate this."
            - Question Length: Long, demanding, and highly detailed (50 to 80 words per question) to set up complex engineering environments.
            """
        elif "INTERMEDIATE" in level or "MID" in level:
            behavior_rules = """
            - Persona: Practical, mid-level engineering lead looking for production readiness.
            - Question Style: Focus on real-world application, common errors, bug debugging, performance tradeoffs, and handling asynchronous data flows or scope challenges.
            - Example Format: "Given a production scenario where script X is causing a memory freeze or failing to bind scope correctly, how would you troubleshoot or optimize it?"
            - Question Length: Moderate (30 to 40 words), introducing a slight situational context.
            """
        else:
            # Bulletproof fallback for BEGINNER or EASY tiers
            behavior_rules = """
            - Persona: Encouraging, straightforward, and foundational.
            - Question Style: Focus purely on vocabulary, base syntax rules, definitions, and standard built-in functions. 
            - Example Format: "What is the purpose of the array method X, and how does it differ from method Y?"
            - Question Length: Keep questions short, clean, and direct (under 20 words).
            """

        # Combine your inputs into the final strict generation instructions
        prompt = f"""
        You are a world-class technical interviewer compiling a customized exam paper. 
        Generate exactly {num_questions} high-quality technical interview questions regarding the subject of '{subject}'.
        
        You must strictly adapt your writing depth, syntax analysis complexity, and length based on these specific rules:
        {behavior_rules}

        Return ONLY a valid JSON list of strings containing the questions exactly like this format: 
        ["Question 1", "Question 2"]
        """
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            questions = json.loads(response.choices[0].message.content)
            
            # 🚀 LIVE TERMINAL LOGS METRICS PRINTER
            print("\n" + "="*50)
            print(f"📡 [LIVE LOG] TESTING LEVEL DETECTED: {level}")
            print(f"📝 QUESTIONS GENERATED BY MODEL:")
            for idx, q in enumerate(questions):
                print(f"   {idx+1}. {q}")
            print("="*50 + "\n")

            if isinstance(questions, dict):
                questions = next(iter(questions.values()))
            if not isinstance(questions, list):
                questions = [str(questions)]
                
        except Exception as e:
            print(f"!!! Generation Error: {e}")
            questions = [f"Explain core concepts of {subject}.", f"What are common design patterns or bugs in {subject}?"]

        # Step 2: Send those questions directly into your interview screen
        return render_template("interview.html", name=name, subject=subject, questions=questions)
        
    return render_template("student.html")

@app.route('/submit', methods=['POST'])
def submit():
    """Processes responses on-the-fly and builds scorecard reports"""
    name = request.form.get('name')
    subject = request.form.get('subject')
    questions = request.form.getlist('questions')
    answers = request.form.getlist('answers')

    result_data = []
    total_score = 0

    for q, a in zip(questions, answers):
        # Call external evaluator utility module
        eval_report = evaluate_answer(
            question=q, 
            user_answer=a, 
            correct_answer="Standard developer guidelines apply."
        )
        
        # Extract the score and feedback text values out safely
        marks = int(eval_report.get('score', 5))
        feedback = eval_report.get('feedback', 'Completed.')

        total_score += marks
        result_data.append({
            "question": q,
            "student_answer": a if a.strip() else "[No Answer Provided]",
            "correct_answer": "Standard developer guidelines apply.",
            "feedback": feedback,
            "marks": marks
        })

    # Calculate final percentage matching ledger template needs
    max_possible = len(questions) * 10
    calculated_pct = round((total_score / max_possible) * 100, 1) if max_possible > 0 else 0
    
    # Map status for admin dashboard
    performance_status = "Passed" if calculated_pct >= 60 else "Needs Improvement"

    # Packing properties to align with admin dashboard layout elements
    interview_data = {
        "name": name,
        "subject": subject,
        "score": calculated_pct,
        "final_score": f"{calculated_pct}%",
        "status": performance_status,
        "performance": performance_status,
        "date": str(datetime.now().strftime("%Y-%m-%d %H:%M")),
        "results": result_data
    }

    # Use safe handlers to append data without risk of creating extra data errors
    interviews = load_json_safely(INTERVIEW_FILE)
    interviews.append(interview_data)
    save_json_safely(INTERVIEW_FILE, interviews)

    return render_template("result.html", data=interview_data)


# ==============================================================================
# 🎙️ MICROSOFT EDGE TTS ENGINE (100% FREE, DISTINCT MALE & FEMALE VOICES)
# ==============================================================================
import asyncio
import edge_tts

# We are using high-fidelity Microsoft Azure neural voices available for free
VOICE_MAPPING = {
    "female1": "en-US-AvaNeural",       # Female 1: Clear American Female
    "female2": "en-GB-SoniaNeural",     # Female 2: Crisp British Female
    "male1": "en-US-AndrewNeural",      # Male 1: Clear American Male
    "male2": "en-GB-RyanNeural"         # Male 2: Grounded British Male
}

@app.route('/api/tts', methods=['POST'])
def text_to_speech_api():
    """Streams crystal-clear, distinct Male and Female voices natively"""
    try:
        data = request.json or {}
        text_content = data.get('text', '')
        voice_profile = data.get('voice', 'female1')
        
        # Pull voice identifier safely
        selected_voice = VOICE_MAPPING.get(voice_profile, VOICE_MAPPING['female1'])
        
        # Create the Microsoft audio stream logic loop
        communicate = edge_tts.Communicate(text_content, selected_voice)
        
        # Run the async communication generator inside Flask's synchronous context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(get_audio_bytes(communicate))
        loop.close()
        
        return app.response_class(audio_data, mimetype="audio/mpeg")
        
    except Exception as e:
        print(f"❌ Edge TTS Engine Failure: {e}")
        return jsonify({"error": str(e)}), 500

async def get_audio_bytes(communicate):
    """Helper to compile the chunks from Edge safely into memory"""
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes
# ==============================================================================

@app.route('/admin')
def admin():
    """Renders administrative summary ledger metrics with recent items first"""
    interviews = load_json_safely(INTERVIEW_FILE)
    
    # Reverse the list so the most recent sessions show up first
    recent_interviews = interviews[::-1]
    
    return render_template("admin.html", interviews=recent_interviews)

# ================= REPORT ROUTE ================= #
@app.route('/report', methods=['POST'])
def report():
    """Retrieves detailed question/answer data metrics for a specific user"""
    target_name = request.form.get('name')
    target_date = request.form.get('date')

    interviews = load_json_safely(INTERVIEW_FILE)

    # Search for the target log that matches both user identity and date-timestamp
    matched_interview = None
    for interview in interviews:
        if interview.get('name') == target_name and interview.get('date') == target_date:
            matched_interview = interview
            break

    # If something went wrong, fall back to form parameters
    if not matched_interview:
        matched_interview = {
            "name": target_name,
            "date": target_date,
            "subject": request.form.get('subject', 'N/A'),
            "score": request.form.get('score', '0%'),
            "final_score": request.form.get('score', '0%'),
            "status": request.form.get('performance', 'N/A'),
            "performance": request.form.get('performance', 'N/A'),
            "results": []
        }

    return render_template("report.html", report=matched_interview)

if __name__ == "__main__":
    app.run(debug=True)