"""Tests for the chat endpoints: sending messages, history, and clearing."""
from tests.conftest import upload_file


def test_chat_without_documents_returns_400(client):
    response = client.post("/chat", json={"message": "hello"})

    assert response.status_code == 400
    assert response.json()["error_code"] == "no_documents_indexed"


def test_chat_stream_without_documents_returns_400_not_a_broken_stream(client):
    """The readiness check must happen *before* the SSE stream opens —
    otherwise the client gets a 200 with a malformed/empty stream instead
    of a clean, typed error."""
    response = client.post("/chat/stream", json={"message": "hello"})

    assert response.status_code == 400
    assert response.json()["error_code"] == "no_documents_indexed"


def test_chat_returns_answer_and_citations(client, fake_chat_model, sample_md_path):
    upload_file(client, sample_md_path)

    response = client.post("/chat", json={"message": "What database do we use for billing?"})

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == fake_chat_model.response_text
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["filename"] == "sample.md"
    assert body["conversation_length"] == 2  # user turn + assistant turn


def test_chat_persists_to_history(client, fake_chat_model, sample_md_path):
    upload_file(client, sample_md_path)
    client.post("/chat", json={"message": "What database do we use for billing?"})

    response = client.get("/chat/history")

    messages = response.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == fake_chat_model.response_text


def test_chat_history_is_empty_by_default(client):
    response = client.get("/chat/history")

    assert response.json() == {"messages": []}


def test_clear_chat_empties_history(client, fake_chat_model, sample_md_path):
    upload_file(client, sample_md_path)
    client.post("/chat", json={"message": "What database do we use for billing?"})

    clear_response = client.delete("/chat")
    assert clear_response.status_code == 200

    history_response = client.get("/chat/history")
    assert history_response.json() == {"messages": []}


def test_chat_stream_emits_token_citation_and_done_events(client, fake_chat_model, sample_md_path):
    upload_file(client, sample_md_path)

    with client.stream(
        "POST", "/chat/stream", json={"message": "What database do we use for billing?"}
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        event_types = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_types.append(line.split("event:")[1].strip())

    assert "token" in event_types
    assert "citations" in event_types
    assert event_types[-1] == "done"


def test_chat_stream_persists_full_answer_to_history(client, fake_chat_model, sample_md_path):
    upload_file(client, sample_md_path)

    with client.stream(
        "POST", "/chat/stream", json={"message": "What database do we use for billing?"}
    ) as response:
        for _ in response.iter_lines():
            pass  # drain the stream

    history = client.get("/chat/history").json()["messages"]
    assert len(history) == 2
    # FakeChatModel.stream() yields word-by-word with a trailing space per
    # word, so the assembled text carries one extra trailing space vs. the
    # non-streaming invoke() path — a fixture artifact, not app behavior.
    assert history[1]["content"].strip() == fake_chat_model.response_text.strip()
    assert len(history[1]["citations"]) >= 1


def test_chat_stream_failure_does_not_leave_orphaned_user_turn(client, monkeypatch, sample_md_path):
    """Regression test for audit finding H1: a mid-stream failure previously
    left the user's turn in history with no matching assistant response,
    since only send_message (not send_message_stream) cleaned up on
    failure. A dangling, unanswered user turn corrupts the prompt context
    built for the *next* question."""
    import app.rag.llm as llm_module

    class BrokenStreamingModel:
        def stream(self, messages):
            yield from ()  # yields nothing
            raise RuntimeError("simulated provider connection drop")

    monkeypatch.setattr(llm_module, "get_chat_model", lambda streaming=False: BrokenStreamingModel())
    upload_file(client, sample_md_path)

    with client.stream(
        "POST", "/chat/stream", json={"message": "What database do we use for billing?"}
    ) as response:
        for _ in response.iter_lines():
            pass  # drain the stream (the failure surfaces as an SSE "error" event)

    history = client.get("/chat/history").json()["messages"]
    assert history == [], (
        "A failed streaming request should leave no orphaned user turn in "
        "history — found: " + str(history)
    )


def test_chat_history_is_capped_at_max_chat_history_turns(client, fake_chat_model, sample_md_path, monkeypatch):
    """Regression test for audit finding M1: MAX_CHAT_HISTORY_TURNS was
    defined but never actually used anywhere — history grew unbounded."""
    from app.config import settings

    monkeypatch.setattr(settings, "MAX_CHAT_HISTORY_TURNS", 2)
    upload_file(client, sample_md_path)

    for i in range(5):
        client.post("/chat", json={"message": f"question number {i}"})

    history = client.get("/chat/history").json()["messages"]
    assert len(history) == 4  # 2 turns * (user + assistant)
    # The oldest turns should have been dropped, not the newest.
    assert "question number 4" in history[-2]["content"]


def test_concurrent_chat_requests_second_one_rejected(client, sample_md_path):
    """Regression test for audit finding H2: without a request-level guard,
    two concurrent requests against the single shared conversation history
    could interleave their append calls and corrupt turn ordering. A slow
    fake LLM call (via a real thread, since TestClient requests block their
    calling thread) lets us actually observe the second request being
    rejected while the first is still in flight."""
    import threading
    import time

    import app.rag.llm as llm_module
    from langchain_core.messages import AIMessage

    class SlowChatModel:
        def invoke(self, messages):
            time.sleep(0.3)
            return AIMessage(content="slow answer")

    import app.services.chat_service as chat_service_module

    original_get_chat_model = llm_module.get_chat_model
    llm_module.get_chat_model = lambda streaming=False: SlowChatModel()
    try:
        upload_file(client, sample_md_path)

        results = {}

        def fire(key):
            results[key] = client.post("/chat", json={"message": f"question from {key}"})

        t1 = threading.Thread(target=fire, args=("first",))
        t1.start()
        time.sleep(0.05)  # let the first request acquire the lock
        t2 = threading.Thread(target=fire, args=("second",))
        t2.start()
        t1.join()
        t2.join()

        statuses = {results["first"].status_code, results["second"].status_code}
        assert 200 in statuses
        assert 429 in statuses, (
            f"Expected the second concurrent request to be rejected with 429, "
            f"got statuses: first={results['first'].status_code}, "
            f"second={results['second'].status_code}"
        )
    finally:
        llm_module.get_chat_model = original_get_chat_model
        chat_service_module.chat_service.clear_history()
