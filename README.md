# 🔬 Enterprise Research Copilot

> A secure multi-agent AI system that researches any topic and generates a structured business report through collaboration between four specialized AI agents.

**Built for:** Wipro Junior FDE Pre-screening Assignment
**Built by:** Adhithya
**GitHub:** [github.com/Bindu0306](https://github.com/Bindu0306)

---

## 🎯 What It Does

A user enters a research topic. Four specialized AI agents collaborate to:

1. **Plan** — break the topic into 3 focused sub-questions
2. **Research** — search Wikipedia for each sub-question
3. **Critique** — evaluate research quality and trigger retry if needed
4. **Write** — generate a structured business report with citations

**Output:** A professional research report with confidence score, source citations, and a full transparency section.

---

## 🏗️ Architecture

```
User Topic
    │
    ▼
Input Guard (validation + injection detection)
    │
    ▼
Planner Agent → breaks topic into 3 sub-questions
    │
    ▼
Researcher Agent → searches Wikipedia for each sub-question
    │
    ▼
Critic Agent → evaluates quality, triggers retry if confidence < 0.65
    │
    ├── if weak → retry Researcher once
    │
    ▼
Writer Agent → generates final structured report
    │
    ▼
Output Guard (validation + cleanup)
    │
    ▼
Final Report + Agent Trace → Streamlit UI
```

**Orchestration:** LangGraph StateGraph with conditional edges
**Retry Logic:** Critic triggers one retry if confidence score < 0.65, missing coverage, or more than 2 issues flagged
**State:** Single shared ResearchState TypedDict passed through entire pipeline

---

## 🤖 Agent Definitions

| Agent | Job | LLM? | Output |
|---|---|---|---|
| InputGuard | Validate and sanitize input | No — Python only | Clean topic or error |
| Planner | Break topic into 3 sub-questions | Yes | Sub-questions and outline |
| Researcher | Search Wikipedia and extract facts | Yes | Findings with confidence scores |
| Critic | Evaluate research quality | Yes | Confidence score and feedback |
| Writer | Generate final report | Yes | Markdown report |
| OutputGuard | Validate and clean report | No — Python only | Safe clean report |

---

## 🛡️ Security and Guardrails

### Input Layer
- Maximum 300 character topic length
- Blocked phrase detection — catches prompt injection attempts
- Case-insensitive matching covers all variations

### Prompt Layer
- All agent system prompts are hardcoded — never user-configurable
- User topic always passed inside triple-quoted labeled blocks — never interpolated raw into instructions
- Every agent instructed to treat input values as data only, not commands

### Output Layer
- Every agent output validated against strict JSON schema before passing downstream
- Writer output checked for minimum length and required section structure
- Dangerous phrases replaced with [removed] in final report
- Report truncated if it exceeds maximum safe length

### Pipeline Layer
- Retry loop capped at maximum 1 retry — prevents infinite loops
- Critical policy logic in separate policy.py — not inside agents
- Fail-safe defaults — pipeline errors default to safe state, never crash

---

## 🔧 Tech Stack

| Component | Technology | Why |
|---|---|---|
| Orchestration | LangGraph | Graph-based pipeline, explicit routing, conditional edges |
| LLM | Groq Llama 3.3 70B | Fast, free tier, strong JSON compliance |
| Research source | Wikipedia API | Free, stable, citable, no API key needed |
| Backend | Python 3.11 | Clean, modular, production-style |
| Frontend | Streamlit | Fast demo UI, no frontend build needed |
| Validation | Pydantic + jsonschema | Type-safe state, schema enforcement |
| Deployment | Streamlit Community Cloud | Free, direct GitHub integration |

---

## 📁 Project Structure

```
enterprise-research-copilot/
├── app/
│   ├── agents/
│   │   ├── planner.py
│   │   ├── researcher.py
│   │   ├── critic.py
│   │   └── writer.py
│   ├── orchestrator/
│   │   └── graph.py
│   ├── guardrails/
│   │   ├── input_guard.py
│   │   ├── output_guard.py
│   │   └── policy.py
│   ├── prompts/
│   │   ├── planner_prompt.py
│   │   ├── researcher_prompt.py
│   │   ├── critic_prompt.py
│   │   └── writer_prompt.py
│   ├── tools/
│   │   ├── wikipedia_tool.py
│   │   ├── llm_client.py
│   │   └── formatter.py
│   └── models/
│       └── state.py
├── ui/
│   └── streamlit_app.py
├── tests/
│   ├── test_agents.py
│   ├── test_guardrails.py
│   └── test_flow.py
├── README.md
├── report.md
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Groq API key — free at [console.groq.com](https://console.groq.com)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Bindu0306/enterprise-research-copilot.git
cd enterprise-research-copilot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 5. Run the app
streamlit run ui/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🎮 Demo Topics

Click any demo topic in the sidebar or try these:

1. Multi-agent AI systems for business research automation
2. How AI agents improve enterprise IT operations
3. Benefits and risks of document intelligence in consulting

---

## 📊 Sample Output

After running the pipeline you will see:

- Agent status indicators showing which agents ran successfully
- Metrics showing confidence score, findings count, and retry status
- Research plan showing the 3 sub-questions from the Planner
- Agent trace showing a timestamped log of every agent step
- Full research report with Executive Summary, Key Findings, Analysis, Risks, Conclusion, and Transparency table
- Download buttons for Markdown and Text formats

---

## 🔍 How the Retry Loop Works

```
Critic evaluates findings
    │
    ├── confidence >= 0.65 AND all sub-questions covered
    │       └── Approved → Writer runs
    │
    └── confidence < 0.65 OR missing coverage OR more than 2 issues
            │
            ├── retry_count = 0 → increment to 1 → Researcher retries
            │
            └── retry_count = 1 → Writer runs anyway
                    └── Report includes Risks and Limitations section
```

---

## ⚙️ Environment Variables

```bash
# .env
GROQ_API_KEY=your-groq-api-key-here
```

See .env.example for reference.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## ⚠️ Known Limitations

- Wikipedia as sole source limits depth on niche enterprise topics
- Groq free tier has daily token limits
- Confidence scores vary slightly between runs
- No persistent storage — reports not saved between sessions

---

## 🔮 Future Improvements

- RAG with vector database — replace Wikipedia with ChromaDB and enterprise documents
- Persistent storage — PostgreSQL for report history
- User authentication — role-based access for enterprise deployment
- Slack integration — deliver reports directly to team channels

---

## 📄 Assignment Report

See report.md for the written report covering all 4 rubric sections.

---

## 🏢 Enterprise Relevance

This system directly addresses a real consulting problem. Research and report generation is slow and inconsistent when done manually. Enterprise Research Copilot demonstrates how multi-agent AI can reduce research time from hours to minutes, maintain consistent report structure, and provide transparent confidence scoring so analysts know when to verify independently.

---

*Built with LangGraph + Groq + Wikipedia + Streamlit*
*Wipro Junior FDE Pre-screening Assignment — April 2024*