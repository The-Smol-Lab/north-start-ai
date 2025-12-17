## North Star – AI Retirement Coach

LangGraph-powered, bilingual Streamlit app that interviews users about their retirement goals, infers investment style, and visualizes readiness with actionable suggestions.

### How It Works (Conceptual Overview)
- **Interview Agent (LangGraph):** `StateGraph` with an extractor node (structured Pydantic output via `ChatOpenAI`) and an interviewer node that keeps asking for missing fields until the profile is complete.
- **Streaming UX:** Chat responses and advice stream token-by-token for conversational feel.
- **Financial Modeling:** `calculate_projection` builds yearly balances (nominal vs. real), applies inflation, and estimates safe withdrawal income; `create_chart` renders the projection with Plotly.
- **Bilingual & Multi-currency:** Toggle Thai/English and THB/USD presets; copy uses `TRANS` while currency defaults/rates live in `CURRENCY_CONFIG`.
- **Reporting:** Generates a styled HTML report with key metrics, future “food index”, and advice transcript for download.

### Project Structure
- `app.py` – Streamlit UI, LangGraph nodes, projection math, charting, downloadable report generation.
- `requirements.txt` – Pinned runtime dependencies.
- `Dockerfile` – Container image for running the Streamlit app.
- `tests/` – Pytest coverage for helper functions, markdown cleaning, and streaming helpers.

### Prerequisites
- Python 3.12 (app was validated with `uv run python --version` → 3.12.10).
- `uv` or `pip` for dependency management.
- Graphviz system binaries (installed automatically in the Docker image; on macOS: `brew install graphviz`).
- `OPENROUTER_API_KEY` env var for LLM access.

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
- **Environment:** `OPENROUTER_API_KEY` is required. Optional: set `LANGCHAIN_TRACING_V2` and `LANGCHAIN_API_KEY` if you want LangSmith tracing.
- **Models:** Interview uses `x-ai/grok-4.1-fast` for conversation and `mistralai/ministral-14b-2512` for structured extraction (both via OpenRouter). Adjust in `app.py` if you prefer different models.
- **Currencies:** Defaults/rates live in `CURRENCY_CONFIG`; update benchmarks or add currencies as needed.

### Testing
```bash
cd retirement_agent
uv run pytest
```

### Teaching Tips for Your Video
- Show the **LangGraph state machine** (extractor → interviewer → END) and how `_missing_profile_fields` drives the prompt.
- Highlight **structured output** with `UserProfile` to automatically merge user data.
- Demonstrate **streaming chat** (`stream_chat_response`) and the difference between onboarding chat vs. advice chat.
- Walk through the **projection math** and how inflation/return sliders affect the readiness score and food index.
