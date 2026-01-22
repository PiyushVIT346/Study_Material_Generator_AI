# 🎓 AI Study Assistant

**Agentic Educational Workflows Powered by LangGraph & Groq**

An intelligent, stateful learning platform that transforms any topic into a structured course. Unlike static generators, this assistant uses **Agentic Workflows** to research, structure, and validate educational content before generating a personalized study guide and a difficulty-adjusted final quiz.

---

## 🚀 System Overview

The **AI Study Assistant** leverages a **Directed Acyclic Graph (DAG)** architecture to manage the lifecycle of a learning session. It transitions through discrete states—from initial topic ingestion to multi-level subtopic generation—ensuring that the final output is contextually accurate for the user’s chosen difficulty level:

- **Beginner**
- **Intermediate**
- **Advanced**

---

## ✨ Key Features

- 🧠 **Agentic State Management**  
  Built with **LangGraph**, enabling complex branching workflows and human-in-the-loop validation.

- 📈 **Adaptive Difficulty Scaling**
  - **Beginner**: Fundamentals explained using analogies with **10 basic questions**
  - **Intermediate**: Balanced theory with **15 application-based questions**
  - **Advanced**: Deep insights, complex applications, and **20 numerically intensive questions**

- 🛠 **Forgiving JSON Parsing**  
  Custom regex-based parsing logic repairs malformed LLM outputs, ensuring **100% system uptime** even with inconsistent AI responses.

- 📝 **Interactive Courseware**  
  Generates structured JSON-based study materials including:
  - Definitions
  - Key concepts
  - Practical examples
  - Visual text-based diagrams

- 🎯 **Automated Quiz Engine**  
  Real-time generation of MCQs with **detailed explanations for every answer**.

---

## 🛠 Technical Architecture

### 1. Agentic Workflow (LangGraph)

The core logic is implemented using a **StateGraph**, which manages the `LearnState`.

```python
class LearnState(TypedDict, total=False):
    current_topic: str
    subtopics: str
    approved: bool
    difficulty: str
```
## 🔁 Node Sequence

The agentic workflow follows a clear, state-driven execution order:

1. **get_topic**  
   Captures user intent, topic selection, and learning constraints.

2. **generate_subtopics**  
   The agent researches the topic and proposes a structured **10-point curriculum**.

3. **generate_study**  
   Generates high-density educational content and stores it in `study_material.json`.

4. **generate_quiz**  
   Extracts knowledge and creates assessment questions in `quiz_final.json`.

---

## 🧰 Tech Stack

| Component      | Technology            | Role                                   |
|----------------|------------------------|----------------------------------------|
| Backend        | Flask                  | Web server & session management         |
| Orchestrator   | LangGraph              | State machine & agentic loops           |
| LLM Provider   | Groq (Llama3-70B)      | High-speed inference & reasoning        |
| Persistence    | JSON / File System     | Local storage for study & quiz data     |
| Core Logic     | Python 3.10            | Application processing                 |

---

## 🚦 Getting Started

### Prerequisites

- **Python 3.10+**
- **Groq API Key**  
  Sign up at: https://console.groq.com

---

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/YourUsername/ai-study-assistant.git
cd ai-study-assistant
```

### 2. Set Environment Variables

Configure your Groq API key as an environment variable:

```bash
export GROQ_API_KEY='your_api_key_here'
```
### 3. Install Dependencies

Install the required Python packages using pip:

```bash
pip install flask langgraph langchain_groq pydantic
```
### 4. Launch the Application

Start the Flask application:

```bash
python app.py
```
Open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

## 🔌 API & Routing

| Endpoint         | Method | Purpose                                  |
|------------------|--------|------------------------------------------|
| `/`              | GET    | Landing page                             |
| `/get-started`   | POST   | Ingests topic & difficulty level         |
| `/confirm-topic` | POST   | Triggers LangGraph execution loop        |
| `/course`        | GET    | Renders generated study material         |
| `/quiz`          | GET    | Starts interactive assessment            |
| `/submit`        | POST   | Calculates score and provides feedback   |

## 🛡 System Resilience
The system includes a `try_parse_json_forgiving` utility designed to:
* Strip Markdown code blocks (`` ```json ``).
* Auto-fix missing quotes on keys.
* Remove trailing commas that break standard `json.loads()`.
* Sanitize smart-quotes (“ ”) to standard double quotes.
