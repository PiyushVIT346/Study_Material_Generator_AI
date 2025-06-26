from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict
import os
import json
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

llm = ChatGroq(model="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"))

STUDY_FILE = "study_material.json"
QUIZ_FILE = "quiz_final.json"

class LearnState(TypedDict, total=False):
    current_topic: str
    subtopics: str
    approved: bool
    difficulty: str

def get_user_topic(state: LearnState) -> LearnState:
    return state

def generate_subtopics(state: LearnState) -> LearnState:
    topic = state["current_topic"]
    difficulty = state["difficulty"]
    prompt = f"""List 10 important subtopics to cover in detail for: {topic} 
    at {difficulty} level. Return as a numbered list with brief descriptions."""
    response = llm.invoke(prompt)
    return {
        **state,
        "subtopics": response.content,
        "approved": True
    }

def try_parse_json_forgiving(bad_json: str) -> dict:
    bad_json = re.sub(r"```(?:json)?", "", bad_json)
    bracket_count = 0
    json_start = -1
    json_end = -1

    for i, char in enumerate(bad_json):
        if char == '{':
            if bracket_count == 0:
                json_start = i
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                json_end = i
                break

    if json_start == -1 or json_end == -1:
        raise ValueError("No valid JSON object found")

    json_string = bad_json[json_start:json_end + 1]
    json_string = re.sub(r'(?<={|,)\s*([\w\s]+?)\s*:', r'"\1":', json_string)
    json_string = re.sub(r",\s*([}\]])", r"\1", json_string)
    json_string = json_string.replace("“", "\"").replace("”", "\"")

    return json.loads(json_string)


def generate_study_material(state: LearnState) -> LearnState:
    topic = state["current_topic"]
    subtopics = state["subtopics"]
    difficulty = state["difficulty"]

    prompt = f"""
You are an educational assistant.

Generate a comprehensive {difficulty}-level study guide for the topic: "{topic}", covering the following subtopics:
{subtopics}

Respond strictly in this JSON format (use real subtopic names as keys):

{{
  "Subtopic Name": {{
    "name": "Subtopic Name",
    "Definition": "Definition suitable for {difficulty} level",
    "Key Concepts": [
      "Concept 1",
      "Concept 2",
      "Concept 3"
    ],
    "Practical Example": "Example relevant for {difficulty} learners",
    "Visual Diagram": "Textual description of a diagram",
    "Summary Points": "Brief bullet-style summary"
  }}
}}

⚠️ FORMAT RULES:
- Return ONLY valid JSON
- No markdown (no ```json)
- All keys and strings MUST be in double quotes
- No trailing commas
"""

    study_content = llm.invoke(prompt).content.strip()

    try:
        study_data = try_parse_json_forgiving(study_content)
    except Exception as e:
        with open("bad_study_output.txt", "w", encoding="utf-8") as f:
            f.write(study_content)
        print("[ JSON ERROR]", e)
        raise ValueError("Failed to parse study material JSON. Check 'bad_study_output.txt' for raw output.")

    with open(STUDY_FILE, "w", encoding="utf-8") as f:
        json.dump(study_data, f, indent=4, ensure_ascii=False)

    return state

def generate_quiz(state: LearnState) -> LearnState:
    """
    Generate quiz questions based on study content and save to JSON file.
    
    Args:
        state: LearnState containing difficulty level
        
    Returns:
        LearnState: Updated state object
    """
    with open(STUDY_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    difficulty = state["difficulty"]
    question_count = 20 if difficulty == "advanced" else 15 if difficulty == "intermediate" else 10
    question_type = (
        "complex numerical" if difficulty == "advanced" else 
        "basic calculation" if difficulty == "beginner" else 
        "balanced conceptual and application-based"
    )
    
    prompt = f"""
You are a helpful quiz generator. Based on the following study content, generate {question_count} multiple-choice questions.

Content: {content}

Generate questions that are {question_type} in nature for {difficulty} level.

Respond strictly in this JSON format as an array of question objects:

[
    {{
        "question": "Sample question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "explanation": "Brief explanation of why this is correct"
    }}
]

CRITICAL REQUIREMENTS:
- Return ONLY a valid JSON array
- No additional text, comments, or markdown
- No ```json code blocks
- Do NOT wrap the JSON in quotes
- All strings must use double quotes
- No trailing commas
- Must be parseable with json.loads()
- Start directly with [ and end with ]
"""

    try:
        quiz_content = llm.invoke(prompt).content
        if quiz_content.startswith('"') and quiz_content.endswith('"'):
            quiz_content = quiz_content[1:-1].replace('\\"', '"').replace('\\n', '\n')
        quiz_data = json.loads(quiz_content)

        with open("quiz_final.json", "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, indent=4, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        raise
    except Exception as e:
        print(f"Error generating quiz: {e}")
        raise

    return state

# LangGraph setup
graph = StateGraph(LearnState)
graph.add_node("get_topic", get_user_topic)
graph.add_node("generate_subtopics", generate_subtopics)
graph.add_node("generate_study", generate_study_material)
graph.add_node("generate_quiz", generate_quiz)

graph.set_entry_point("get_topic")
graph.add_edge("get_topic", "generate_subtopics")
graph.add_edge("generate_subtopics", "generate_study")
graph.add_edge("generate_study", "generate_quiz")
graph.add_edge("generate_quiz", END)

compiled_graph = graph.compile()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-started', methods=['GET', 'POST'])
def get_started():
    if request.method == 'POST':
        session['topic'] = request.form['topic']
        session['difficulty'] = request.form.get('difficulty', 'intermediate')
        return redirect(url_for('confirm_topic'))
    return render_template('get_started.html')

@app.route('/confirm-topic', methods=['GET', 'POST'])
def confirm_topic():
    topic = session.get('topic', '')
    difficulty = session.get('difficulty', 'intermediate')
    if request.method == 'POST':

        user_state = {
            "current_topic": topic,
            "subtopics": "",
            "approved": False,
            "difficulty": difficulty
        }
        compiled_graph.invoke(user_state)
        return redirect(url_for('course_page'))
    return render_template('confirm_topic.html', topic=topic, difficulty=difficulty)

@app.route('/course')
def course_page():
    try:
        with open(STUDY_FILE, 'r', encoding='utf-8') as f:
            content=json.load(f)
    except FileNotFoundError:
        content = "Study material not found."
    return render_template('course.html', study_data=content)

@app.route('/quiz')
def quiz_page():
    try:
        with open("quiz_final.json", 'r', encoding='utf-8') as f:
            quiz = json.load(f)
    except FileNotFoundError:
        quiz = []
    except json.JSONDecodeError:
        quiz = []

    return render_template('quiz.html', quiz=quiz)

from flask import request

@app.route('/submit', methods=['POST'])
def submit_quiz():
    with open("quiz_final.json", 'r', encoding='utf-8') as f:
        quiz = json.load(f)

    score = 0
    total = len(quiz)
    answers = []

    for idx, q in enumerate(quiz):
        selected = request.form.get(f'q{idx}')
        correct = q['correct_answer']
        is_correct = selected == correct
        if is_correct:
            score += 1
        answers.append({
            'question': q['question'],
            'selected': selected,
            'correct': correct,
            'is_correct': is_correct
        })

    return render_template('result.html', score=score, total=total, answers=answers)

if __name__ == '__main__':
    app.run(debug=True)
