from app.graph import PIPELINE, build_graph, next_stage


def _recording_nodes(calls, failing=None):
    def make(name):
        def node(state):
            calls.append(name)
            return {"errors": [f"{name} failed"]} if name == failing else {}

        return node

    return {name: make(name) for name in PIPELINE}


def test_each_agent_runs_exactly_once_in_order():
    calls = []
    build_graph(_recording_nodes(calls)).invoke({"errors": []})
    assert calls == list(PIPELINE)


def test_pipeline_stops_at_the_first_failure():
    calls = []
    final = build_graph(_recording_nodes(calls, failing="analyst")).invoke({"errors": []})
    assert calls == ["retriever", "analyst"]
    assert final["errors"] == ["analyst failed"]


def test_next_stage():
    assert next_stage("retriever") == "analyst"
    assert next_stage("report") is None
