import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app


@pytest.fixture(autouse=True)
def reset_session_state():
    st.session_state.clear()


@pytest.fixture
def app_module():
    return importlib.reload(app)


def test_extraction_node_no_api_key_returns_state(app_module, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    state = {"messages": [], "profile": {}, "language": "EN", "currency": "USD", "is_complete": False}

    result = app_module.extraction_node(state)

    assert result is state


def test_extraction_node_merges_profile_and_flags_complete(app_module, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class StructuredMock:
        def __init__(self, payload):
            self.payload = payload

        def invoke(self, messages):
            class Profile:
                def __init__(self, payload):
                    self.payload = payload

                def model_dump(self, exclude_none=False):
                    return self.payload

            return Profile(self.payload)

    class ChatMock:
        def __init__(self, *args, **kwargs):
            pass

        def with_structured_output(self, model):
            return StructuredMock(
                {
                    "age": 35,
                    "retirement_age": 60,
                    "current_savings": 50000.0,
                    "monthly_savings": 2000.0,
                    "target_monthly_expense": 1800.0,
                    "investment_style": "Bank/Cash",
                }
            )

    monkeypatch.setattr(app_module, "ChatOpenAI", ChatMock)

    state = {
        "messages": [app_module.HumanMessage(content="I save at the bank")],
        "profile": {"age": 30},
        "language": "EN",
        "currency": "USD",
        "is_complete": False,
    }

    result = app_module.extraction_node(state)

    assert result["is_complete"] is True
    assert result["profile"]["age"] == 35
    assert result["profile"]["monthly_savings"] == 2000.0
    assert result["profile"]["investment_style"] == "Bank/Cash"


def test_conversational_node_returns_ready_when_complete(app_module):
    state = {
        "messages": [app_module.HumanMessage(content="All done")],
        "profile": {},
        "language": "EN",
        "currency": "USD",
        "is_complete": True,
    }

    result = app_module.conversational_node(state)

    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "CALCULATION_READY"


def test_conversational_node_captures_missing_fields_in_prompt(app_module, monkeypatch):
    captured = {}

    class ChatMock:
        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, messages):
            captured["prompt"] = messages[0].content
            return app_module.AIMessage(content="next question")

    monkeypatch.setattr(app_module, "ChatOpenAI", ChatMock)
    monkeypatch.setenv("OPENROUTER_API_KEY", "abc123")

    state = {
        "messages": [app_module.HumanMessage(content="Hi")],
        "profile": {},
        "language": "EN",
        "currency": "USD",
        "is_complete": False,
    }

    result = app_module.conversational_node(state)

    assert "Missing Data" in captured["prompt"]
    assert "Current Age" in captured["prompt"]
    assert "Desired Retirement Lifestyle" in captured["prompt"]
    assert isinstance(result["messages"][0], app_module.AIMessage)


def test_build_interview_graph_wires_nodes(app_module, monkeypatch):
    class GraphSpy(app_module.StateGraph):
        def __init__(self, *_):
            super().__init__()

    monkeypatch.setattr(app_module, "StateGraph", GraphSpy)

    workflow = app_module.build_interview_graph()

    assert workflow["entry"] == "extractor"
    assert ("extractor", app_module.extraction_node) in workflow["nodes"]
    assert ("interviewer", app_module.conversational_node) in workflow["nodes"]
    assert ("extractor", "interviewer") in workflow["edges"]
    assert ("interviewer", app_module.END) in workflow["edges"]


def test_calculate_projection_returns_expected_rows(app_module):
    df = app_module.calculate_projection(
        age=30, retire_age=32, current=1000.0, monthly=100.0, rate=10.0, inflation=2.0, growth=0.0, currency="THB"
    )

    assert list(df["Age"]) == [30, 31, 32]
    assert pytest.approx(df.iloc[0]["Real"], rel=1e-5) == 1000.0
    assert df.iloc[-1]["Nominal"] > df.iloc[0]["Nominal"]


def test_create_chart_adds_traces_and_hline(app_module):
    df = pd.DataFrame({"Age": [30, 31], "Real": [1000, 1100], "Nominal": [1000, 1200]})

    fig = app_module.create_chart(df, target_monthly=1000, currency="USD")

    assert len(fig.data) == 2
    assert fig.data[0].kwargs["x"].equals(df["Age"])
    target_pv = (1000 * 12) / 0.04
    assert fig.layout["shapes"][0]["y0"] == target_pv


def test_create_gauge_sets_color_based_on_score(app_module):
    low = app_module.create_gauge(20, {"rep_score": "Score"})
    mid = app_module.create_gauge(65, {"rep_score": "Score"})
    high = app_module.create_gauge(90, {"rep_score": "Score"})

    assert low.data[0].kwargs["gauge"]["bar"]["color"] == "red"
    assert mid.data[0].kwargs["gauge"]["bar"]["color"] == "#FFC107"
    assert high.data[0].kwargs["gauge"]["bar"]["color"] == "#00CC96"


def test_get_advice_without_api_key_returns_error(app_module, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    message = app_module.get_advice({"monthly_shortfall_gap": 0}, [], "EN", "USD")

    assert "Configuration Error" in message


def test_get_advice_calls_llm_when_key_present(app_module, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")

    class AdviceChat:
        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, messages):
            return app_module.AIMessage(content="personalized advice")

    monkeypatch.setattr(app_module, "ChatOpenAI", AdviceChat)
    app_module.curr_conf = app_module.CURRENCY_CONFIG["USD"]

    profile = {"monthly_shortfall_gap": 500, "investment_style": "Bank/Cash"}
    history = [app_module.HumanMessage(content="Need help")]

    advice = app_module.get_advice(profile, history, "EN", "USD")

    assert advice == "personalized advice"


def test_clean_markdown_table_inserts_spacing(app_module):
    raw = "- item\n| C1 | C2 |\n| --- | --- |\n| A | B |\nNext"

    cleaned = app_module.clean_markdown_table(raw)

    assert cleaned.startswith("- item\n\n\n| C1 | C2 |\n")


def test_clean_markdown_table_unwraps_fenced_block(app_module):
    raw = "```\n| A | B |\n| --- | --- |\n| 1 | 2 |\n```"

    cleaned = app_module.clean_markdown_table(raw)

    assert "```" not in cleaned
    assert cleaned.lstrip().startswith("| A | B |")


def test_generate_html_report_includes_content(app_module):
    profile = {
        "age": 30,
        "retirement_age": 60,
        "current_savings": 100000,
        "monthly_savings": 2000,
        "investment_style": "Bank/Cash",
    }
    assumptions = {"rate": 5.0, "inflation": 2.0, "growth": 1.0}
    advice_history = [app_module.HumanMessage(content="Tell me more"), app_module.AIMessage(content="Stay diversified")]
    fig = app_module.go.Figure()

    html = app_module.generate_html_report(
        profile,
        assumptions,
        safe_income=1200,
        target_expense=1000,
        food_price=75,
        score=80,
        advice_history=advice_history,
        fig=fig,
        lang="EN",
        currency="USD",
    )

    assert "Financial Freedom Report" in html
    assert "$1,200" in html
    assert "Stay diversified" in html
    assert "<div>figure</div>" in html
