from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
import os
from typing import TypedDict

# ✅ Load environment variable
llm = ChatGroq(model="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"))

# Global file names
STUDY_FILE = "study_material.txt"
QUIZ_FILE = "quiz.txt"

# 📘 LangGraph state schema
class LearnState(TypedDict, total=False):
    current_topic: str
    subtopics: str
    approved: bool
    difficulty: str  # New field for difficulty level

# Initialize with required fields
initial_state = {
    "current_topic": "",
    "subtopics": "",
    "approved": False,
    "difficulty": "intermediate"  # Default value
}

# Step 1: Ask user for main topic and difficulty
def get_user_topic(state: LearnState) -> LearnState:
    topic = input("\nEnter the topic you want to study: ").strip()
    print("\nSelect difficulty level:")
    print("1. Beginner")
    print("2. Intermediate")
    print("3. Advanced")
    difficulty_choice = input("Enter choice (1-3): ").strip()
    
    difficulty_map = {
        "1": "beginner",
        "2": "intermediate",
        "3": "advanced"
    }
    difficulty = difficulty_map.get(difficulty_choice, "intermediate")
    
    return {
        **state,
        "current_topic": topic,
        "difficulty": difficulty,
        "approved": False
    }

# Step 2: Generate related subtopics
def generate_subtopics(state: LearnState) -> LearnState:
    topic = state["current_topic"]
    difficulty = state["difficulty"]
    prompt = f"""List 5 important subtopics to cover in detail for: {topic} 
    at {difficulty} level. Return as a numbered list with brief descriptions."""
    response = llm.invoke(prompt)
    return {
        **state,
        "subtopics": response.content
    }

# Step 3: Ask user to approve subtopics
def confirm_subtopics(state: LearnState) -> LearnState:
    print("\n📚 Suggested Subtopics:")
    print(state["subtopics"])
    choice = input("\nAre these subtopics okay? (yes/no): ").strip().lower()
    return {
        **state,
        "approved": choice == "yes"
    }

# Step 4: Generate study material with difficulty consideration
def generate_study_material(state: LearnState) -> LearnState:
    topic = state["current_topic"]
    subtopics = state["subtopics"]
    difficulty = state["difficulty"]
    
    prompt = f"""
Create a comprehensive {difficulty}-level study guide for: {topic}
Cover these subtopics in detail:
{subtopics}

The content should be tailored for {difficulty} learners:
- For beginner: Explain fundamentals with simple analogies
- For intermediate: Balance theory and practical applications
- For advanced: Include deep insights and complex applications

Include:
- Clear definitions appropriate for {difficulty} level
- Key concepts with suitable depth
- Practical examples matching the difficulty
- Visual diagrams (described in text)
- Summary points
"""
    study_content = llm.invoke(prompt).content
    with open(STUDY_FILE, "w", encoding="utf-8") as f:
        f.write(study_content)
    print(f"\n✅ Study material saved to {STUDY_FILE}")
    return state

# Step 5: Generate quiz with difficulty consideration
def generate_quiz(state: LearnState) -> LearnState:
    with open(STUDY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    difficulty = state["difficulty"]
    question_count = 20 if difficulty == "advanced" else 15 if difficulty == "intermediate" else 10
    
    prompt = f"""
Based on this {difficulty}-level study content:
{content}

Generate:
1. {question_count} multiple-choice questions (4 options each) appropriate for {difficulty} level
2. Clearly mark the correct answer
3. Include a mix of:
   - Conceptual questions
   - {'Complex numerical problems' if difficulty == 'advanced' else 'Basic calculations' if difficulty == 'beginner' else 'Balanced mix'}
   - Application-based scenarios
4. Include detailed explanations for each answer
5. Format with clear question numbering
"""
    quiz_content = llm.invoke(prompt).content
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        f.write(quiz_content)
    print(f"\n✅ Quiz saved to {QUIZ_FILE}")
    return state

# 🧠 Build LangGraph
graph = StateGraph(LearnState)

# Add nodes
graph.add_node("get_topic", get_user_topic)
graph.add_node("generate_subtopics", generate_subtopics)
graph.add_node("confirm_subtopics", confirm_subtopics)
graph.add_node("generate_study", generate_study_material)
graph.add_node("generate_quiz", generate_quiz)

# Add edges
graph.set_entry_point("get_topic")
graph.add_edge("get_topic", "generate_subtopics")
graph.add_edge("generate_subtopics", "confirm_subtopics")

# Conditional edges
graph.add_conditional_edges(
    "confirm_subtopics",
    lambda state: "generate_study" if state["approved"] else "generate_subtopics"
)
graph.add_edge("generate_study", "generate_quiz")
graph.add_edge("generate_quiz", END)

# Compile and run
app = graph.compile()

if __name__ == "__main__":
    print("🌟 AI Study Assistant 🌟")
    print("-----------------------")
    app.invoke(initial_state)
    print("\n🎉 Learning session complete! 🎉")