import asyncio
import importlib
import sys
from pathlib import Path

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


def test_stream_chat_response_yields_and_accumulates(app_module):
    class FakeChunk:
        def __init__(self, content):
            self.content = content

    class FakeLLM:
        def __init__(self):
            self.seen_messages = None

        async def astream(self, messages):
            self.seen_messages = messages
            for piece in ["Hello", " world"]:
                yield FakeChunk(piece)

    llm = FakeLLM()
    updates = []

    def capture(delta, full):
        updates.append((delta, full))

    result = asyncio.run(
        app_module.stream_chat_response(
            llm, [app_module.HumanMessage(content="hi")], on_token=capture
        )
    )

    assert result == "Hello world"
    assert updates[0][0] == "Hello"
    assert updates[-1][1] == "Hello world"
    assert llm.seen_messages[0].content == "hi"
