# LearnWise AI Auto-Improvement Service

A production-ready FastAPI service that implements a self-healing LLM pipeline. It performs structured IT Support Ticket classification using a smaller "Student" LLM and features an automated, asynchronous Auto-Improvement loop driven by a more powerful "Professor" LLM to evaluate, correct, and dynamically update prompts without degrading existing performance.

## 🚀 Key Architectural Features

* **Self-Improving Prompt Mechanism (Mini-Batch):** Instead of overfitting to single errors, the system batches failed inferences and generates optimized prompts handling multiple edge cases simultaneously.
* **Deterministic Regression Testing:** Leverages strict Pydantic V2 Enums and Booleans to evaluate regressions mathematically (`response == expected`), eliminating the need for fuzzy semantic evaluation or secondary LLM judges.
* **Resilient LLM Integration:** Features built-in robust JSON parsing (Markdown stripping) to handle open-source model hallucinations and implements Exponential Backoff to gracefully survive API rate limits (e.g., `429 Too Many Requests`).
* **Clean Architecture & SOLID Principles:** Heavily relies on Dependency Injection (FastAPI `Depends`) and Python `Protocol` interfaces, ensuring the infrastructure (SQLite/Groq) is completely decoupled from the business logic.
* **Centralized Global Error Handling:** Domain logic remains clean from defensive `try/except` boilerplate. Unhandled errors bubble up to centralized hooks that log contextually and return standardized HTTP responses.
* **Idempotent Application Lifespan:** Database creation and initial seeding (Master Prompt & Golden Dataset) run safely within the FastAPI asynchronous lifespan, ensuring the app is container-ready.

## 🛠️ Tech Stack

* **Core:** Python 3.12+, FastAPI, Uvicorn, Asyncio
* **Data Validation:** Pydantic V2
* **Database:** SQLite (async), SQLModel, SQLAlchemy
* **AI Integration:** Groq API (Llama-3-8B / 70B) / Google Gemini API via custom abstract interfaces

## 📂 Project Structure

```text
├── src/
│   ├── api/               # FastAPI Routers, Dependencies, and Global Error Handlers
│   ├── config/            # Pydantic BaseSettings (.env loading)
│   ├── core/              # System Logger, Custom Exceptions, Async SQLite Config
│   ├── interfaces/        # Protocols (ILLMClient, ITicketStorage)
│   ├── llm/               # Concrete LLM Clients (Groq, Gemini)
│   ├── models/            # SQLModel Database Entities & Pydantic Schemas
│   ├── services/          # Business Logic (Inference, Review, Regression)
│   ├── workers/           # Background Tasks (Review Pipeline triggering)
│   └── main.py            # FastAPI App Factory & Lifespan Hooks
├── scripts/
│   └── seed_db.py         # Idempotent Golden Dataset and Initial Prompt seeding
├── tests/                 # Unit & E2E Pytest suite
├── system.log             # Persistent application logs
├── .env                   # Environment variables
└── README.md
```

## ⚙️ Getting Started

### 1. Prerequisites
Ensure you have Python 3.12+ installed. Create a virtual environment and install the requirements.txt (e.g., via `pip` or `poetry`).

### 2. Environment Variables
Create a `.env` file in the root directory based on the following template:

```env
# API Keys
GROQ_API_KEY="your_groq_api_key_here"

# Database
DATABASE_URL="sqlite+aiosqlite:///tickets.db"

# LLM Configuration
LLM_PROVIDER="groq" # Options: groq, gemini

# Auto-Improvement Configuration
REVIEW_BATCH_SIZE=20          # How much are we reviewing max REVIEW_TRIGGER_LIMIT=20       # Wait for X tickets to trigger review
MAX_GOLDEN_SAMPLES=15         # FIFO limit for the Golden Dataset
MIN_REGRESSION_ACCURACY=1.0   # Required pass rate for new prompts (0.0 to 1.0)
MAX_PROMPT_RETRIES=2          # Retries allowed if the new prompt fails regression
```

### 3. Running the Server
Start the application using Uvicorn. 

```bash
uvicorn src.main:app --reload 
```
*Upon startup, the FastAPI `lifespan` will automatically create the SQLite tables and seed the database with the initial prompt and base Golden Samples.*

## 🔌 API Usage

### `POST /process`
Main inference endpoint. Analyzes the user's input, classifies the IT support ticket using the currently active Prompt Version, and returns a strictly validated JSON structure.

**Request:**
```json
{
  "text": "I've been charged twice for my subscription this month and I want a refund now."
}
```

**Response (200 OK):**
```json
{
  "intent": "billing_issue",
  "urgency": "high",
  "affected_component": "backend_api",
  "requires_manager_escalation": false
}
```

## 🧠 The Auto-Improvement Lifecycle

1. **Inference & State Management:** Every call to `/process` is logged into the `TicketSample` table. A thread-safe Singleton (`SystemStateManager`) increments the process counter.
2. **Background Trigger:** When the counter hits `REVIEW_TRIGGER_LIMIT`, FastAPI dispatches the `ReviewService` in a background task.
3. **Evaluation (The Professor):** The Service fetches unevaluated tickets. The LLM acts as a Judge, flagging errors and providing the `expected_output` for failed inferences.
4. **Golden Dataset Protection:** Failed samples are promoted to the Golden Dataset. A strict FIFO algorithm maintains the dataset size under `MAX_GOLDEN_SAMPLES`, ensuring base-cases are never deleted.
5. **Batch Optimization & Retry Loop:** The Professor LLM takes all accumulated failures as context and generates an improved prompt. If the new prompt fails the regression test against the Golden Dataset, the failure context is fed back to the LLM for up to `MAX_PROMPT_RETRIES` attempts before gracefully surrendering and logging the anomaly.