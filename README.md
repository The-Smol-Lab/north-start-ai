## North Star – AI Retirement Coach

LangGraph-powered, bilingual Streamlit app that interviews users about their retirement goals, infers investment style, and visualizes readiness with actionable suggestions.

<img width="2752" height="1536" alt="unnamed (1)" src="https://github.com/user-attachments/assets/64f1ecf1-5a7d-4868-be8d-571e54cca40e" />

### 🚀 Performance & Scalability (Cloud Optimized)

The app is specifically tuned for **Streamlit Community Cloud** to handle concurrent users and stay within the 1GB RAM limit:

* **Execution Sharding (`st.fragment`):** The dashboard and projection sliders are isolated into fragments. Adjusting financial variables only reruns the calculation logic and charts, preventing the entire LLM chat history and sidebar from re-rendering.
* **Computation Caching (`@st.cache_data`):** Mathematical projections are cached based on input parameters. If multiple users input similar retirement goals, the server serves the result from memory instantly.
* **Object Lifecycle Management (`@st.cache_resource`):** Large objects like the LLM connection pool (LangChain ChatOpenAI) and Plotly figure templates are initialized once and shared across sessions to reduce latency.
* **Async Streaming:** Utilizes `asyncio` for non-blocking LLM token streaming, ensuring the UI remains responsive even during heavy inference.

### How It Works (Conceptual Overview)

* **Interview Agent (LangGraph):** `StateGraph` with an extractor node (structured Pydantic output via `ChatOpenAI`) and an interviewer node that keeps asking for missing fields until the profile is complete.
* **Streaming UX:** Chat responses and advice stream token-by-token for conversational feel.
* **Financial Modeling:** `calculate_projection` builds yearly balances (nominal vs. real), applies inflation, and estimates safe withdrawal income.
* **Bilingual & Multi-currency:** Toggle Thai/English and THB/USD presets; copy uses `TRANS` while currency defaults/rates live in `CURRENCY_CONFIG`.
* **Reporting:** Generates a styled HTML report with key metrics, future “food index”, and advice transcript for download.

### Project Structure

* `app.py` – Streamlit UI, LangGraph nodes, projection math, charting, downloadable report generation.
* `requirements.txt` – Pinned runtime dependencies.
* `Dockerfile` – Container image for running the Streamlit app.
* `tests/` – Pytest coverage for helper functions, markdown cleaning, and streaming helpers.

### Prerequisites

* Python 3.12 (app was validated with `uv run python --version` → 3.12.10).
* `uv` or `pip` for dependency management.
* Graphviz system binaries (installed automatically in the Docker image; on macOS: `brew install graphviz`).
* `OPENROUTER_API_KEY` env var for LLM access.

### Local Setup

```bash
cd retirement_agent

# Create virtual env
uv venv

# Install deps (uv recommended)
uv pip install -r requirements.txt

# Run the app
uv run streamlit run app.py

```

### Running with Docker

```bash
cd retirement_agent
docker build -t retirement-agent .
docker run -p 8501:8501 \
  -e OPENROUTER_API_KEY=your_key_here \
  retirement-agent

```

Open http://localhost:8501 to interact with the coach.

### Configuration Notes

* **Environment:** `OPENROUTER_API_KEY` is required. Optional: set `LANGCHAIN_TRACING_V2` and `LANGCHAIN_API_KEY` if you want LangSmith tracing.
* **Models:** Interview uses `x-ai/grok-4.1-fast` for conversation and `mistralai/ministral-14b-2512` for structured extraction (both via OpenRouter).
* **Secrets (Cloud):** If deploying to Streamlit Cloud, add `OPENROUTER_API_KEY` under **Advanced Settings > Secrets**.

---

**Would you like me to also help you generate a `secrets.toml` example for your local `.streamlit/` folder to make testing easier?**
