import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _DummyContext:
    """Minimal context manager used to stub Streamlit containers/columns."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __getattr__(self, name):
        def _stub(*args, **kwargs):
            if name == "columns":
                count = args[0] if args else kwargs.get("spec", 0)
                count = len(count) if isinstance(count, (list, tuple)) else int(count or 0)
                return [_DummyContext() for _ in range(count)]
            if name == "button":
                return False
            if name == "chat_input":
                return None
            if name == "selectbox":
                options = kwargs.get("options") or (args[1] if len(args) > 1 else [])
                index = kwargs.get("index", 0)
                return options[index] if options else None
            if name == "radio":
                options = kwargs.get("options") or (args[1] if len(args) > 1 else [])
                index = kwargs.get("index", 0)
                return options[index] if options else None
            if name == "number_input":
                if len(args) >= 4:
                    return args[3]
                return kwargs.get("value")
            if name == "slider":
                if len(args) >= 3:
                    return args[2]
                return kwargs.get("value")
            return None

        return _stub

    def write(self, *args, **kwargs):
        return None


class StreamlitStub(types.ModuleType):
    """Lightweight stub to keep Streamlit API calls inert during tests."""

    def __init__(self):
        super().__init__("streamlit")
        self.session_state = {}
        self.sidebar = _DummyContext()

    def __getattr__(self, name):
        if name == "sidebar":
            return self.sidebar
        if name in {"chat_message", "spinner", "container", "expander"}:
            return lambda *a, **k: _DummyContext()
        if name == "columns":
            return lambda spec: [_DummyContext() for _ in range(spec if isinstance(spec, int) else len(spec))]
        if name == "button":
            return lambda *a, **k: False
        if name == "chat_input":
            return lambda *a, **k: None
        if name == "number_input":
            return lambda *a, **k: a[3] if len(a) >= 4 else k.get("value")
        if name == "slider":
            return lambda *a, **k: a[2] if len(a) >= 3 else k.get("value")
        if name == "selectbox":
            return lambda *a, **k: (k.get("options") or (a[1] if len(a) > 1 else []))[k.get("index", 0)] if (k.get("options") or (a[1] if len(a) > 1 else [])) else None
        if name == "radio":
            return lambda *a, **k: (k.get("options") or (a[1] if len(a) > 1 else []))[k.get("index", 0)] if (k.get("options") or (a[1] if len(a) > 1 else [])) else None
        if name in {"markdown", "set_page_config", "progress", "json", "title", "info", "success", "warning", "error", "divider", "download_button", "caption", "plotly_chart", "rerun", "stop"}:
            return lambda *a, **k: None
        return lambda *a, **k: None


class ChatOpenAIStub:
    def __init__(self, *args, **kwargs):
        pass

    def with_structured_output(self, model):
        return self

    def invoke(self, messages):
        return AIMessage(content="stubbed")


class StateGraphStub:
    def __init__(self, *_):
        self.nodes = []
        self.edges = []
        self.entry = None

    def add_node(self, name, fn):
        self.nodes.append((name, fn))

    def add_edge(self, src, dst):
        self.edges.append((src, dst))

    def set_entry_point(self, name):
        self.entry = name

    def compile(self):
        return {"nodes": self.nodes, "edges": self.edges, "entry": self.entry}


class ScatterStub:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class IndicatorStub:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FigureStub:
    def __init__(self, *traces):
        self.data = list(traces)
        self.layout = {"shapes": []}

    def add_trace(self, trace):
        self.data.append(trace)

    def add_hline(self, y=None, line_dash=None, line_color=None, annotation_text=None):
        self.layout.setdefault("shapes", []).append(
            {"y0": y, "y1": y, "line_dash": line_dash, "line_color": line_color, "annotation_text": annotation_text}
        )

    def update_layout(self, **kwargs):
        self.layout.update(kwargs)

    def update_yaxes(self, **kwargs):
        self.layout.setdefault("yaxis", {}).update(kwargs)


def _install_streamlit_stub():
    sys.modules["streamlit"] = StreamlitStub()


def _install_langchain_stubs():
    messages_mod = types.ModuleType("langchain_core.messages")

    class BaseMessage:
        def __init__(self, content=None, **kwargs):
            self.content = content

    class HumanMessage(BaseMessage):
        pass

    class AIMessage(BaseMessage):
        pass

    class SystemMessage(BaseMessage):
        pass

    messages_mod.BaseMessage = BaseMessage
    messages_mod.HumanMessage = HumanMessage
    messages_mod.AIMessage = AIMessage
    messages_mod.SystemMessage = SystemMessage

    lc_core = types.ModuleType("langchain_core")
    lc_core.messages = messages_mod

    sys.modules["langchain_core"] = lc_core
    sys.modules["langchain_core.messages"] = messages_mod

    lc_openai = types.ModuleType("langchain_openai")
    lc_openai.ChatOpenAI = ChatOpenAIStub
    sys.modules["langchain_openai"] = lc_openai

    graph_mod = types.ModuleType("langgraph.graph")
    graph_mod.StateGraph = StateGraphStub
    graph_mod.END = "END"
    langgraph_root = types.ModuleType("langgraph")
    langgraph_root.graph = graph_mod
    sys.modules["langgraph"] = langgraph_root
    sys.modules["langgraph.graph"] = graph_mod


def _install_plotly_stubs():
    go_mod = types.ModuleType("plotly.graph_objects")
    go_mod.Figure = FigureStub
    go_mod.Scatter = ScatterStub
    go_mod.Indicator = IndicatorStub

    io_mod = types.ModuleType("plotly.io")

    def to_html(fig, full_html=False, include_plotlyjs="cdn"):
        return "<div>figure</div>"

    io_mod.to_html = to_html

    plotly_root = types.ModuleType("plotly")
    plotly_root.graph_objects = go_mod
    plotly_root.io = io_mod

    sys.modules["plotly"] = plotly_root
    sys.modules["plotly.graph_objects"] = go_mod
    sys.modules["plotly.io"] = io_mod


_install_streamlit_stub()
_install_langchain_stubs()
_install_plotly_stubs()

# Export stub classes for tests that need direct access.
BaseMessage = sys.modules["langchain_core.messages"].BaseMessage
HumanMessage = sys.modules["langchain_core.messages"].HumanMessage
AIMessage = sys.modules["langchain_core.messages"].AIMessage
SystemMessage = sys.modules["langchain_core.messages"].SystemMessage
ChatOpenAI = sys.modules["langchain_openai"].ChatOpenAI
StateGraph = sys.modules["langgraph.graph"].StateGraph
END = sys.modules["langgraph.graph"].END
Figure = sys.modules["plotly.graph_objects"].Figure
Scatter = sys.modules["plotly.graph_objects"].Scatter
Indicator = sys.modules["plotly.graph_objects"].Indicator
