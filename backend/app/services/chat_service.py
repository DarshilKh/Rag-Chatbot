"""
Chat service — owns conversation state and orchestrates question answering
through the RAG pipeline. Routes never call `rag.pipeline` directly.

Conversation history is kept in-memory (single global conversation, matching
the "Clear chat" feature in the spec). This is intentional: there's no user
auth in scope, so a per-user/session store would be over-engineering here —
swapping this for a per-session store later only means changing this class.
"""
import threading

from app.config import settings
from app.core.exceptions import AppError, ChatBusyError, LLMProviderError, NoDocumentsIndexedError
from app.core.logging import logger
from app.models.chat import ConversationTurn
from app.rag import pipeline as rag_pipeline
from app.services.document_service import document_service

_history_lock = threading.Lock()
# Serializes access to the single shared conversation: two concurrent chat
# requests (e.g. two browser tabs) would otherwise interleave their
# "append user turn -> generate -> append assistant turn" sequences, since
# _history_lock only protects individual list mutations, not that whole
# sequence as one unit — corrupting turn ordering for both requests (audit
# finding H2). A second request arriving while one is in flight gets a
# clear, typed error instead of silently corrupting shared state.
_request_lock = threading.Lock()


class ChatService:
    def __init__(self):
        self._history: list[ConversationTurn] = []

    def get_history(self) -> list[ConversationTurn]:
        with _history_lock:
            return list(self._history)

    def clear_history(self) -> None:
        with _history_lock:
            self._history.clear()
        logger.info("Chat history cleared.")

    def _append_turn(self, turn: ConversationTurn) -> list[ConversationTurn]:
        with _history_lock:
            self._history.append(turn)
            # Cap stored history at MAX_CHAT_HISTORY_TURNS*2 (user+assistant
            # per turn) so a very long-lived process doesn't grow this list
            # (and the O(n) copy taken on every message) without bound
            # (audit finding M1 — this setting was previously dead/unused).
            max_entries = settings.MAX_CHAT_HISTORY_TURNS * 2
            if len(self._history) > max_entries:
                del self._history[: len(self._history) - max_entries]
            return list(self._history)

    def _pop_last_turn(self) -> None:
        with _history_lock:
            if self._history:
                self._history.pop()

    def _ensure_documents_ready(self) -> None:
        documents = document_service.list_documents()
        ready_docs = [d for d in documents if d.status == "ready"]
        if not ready_docs:
            raise NoDocumentsIndexedError(
                "No documents are indexed yet. Upload a document and wait for it to finish "
                "processing before asking questions."
            )

    def validate_ready_for_chat(self) -> None:
        """Exposed separately so routes can check readiness *before* opening
        an SSE stream — once a StreamingResponse's headers are sent, it's too
        late to return a normal 4xx error response."""
        self._ensure_documents_ready()
        if self._is_busy():
            raise ChatBusyError(
                "Still processing a previous message — please wait for it to finish."
            )

    def _is_busy(self) -> bool:
        """Non-blocking probe: true if a chat request is currently in flight.
        This is a best-effort check for returning a clean 429 immediately
        (used by routes before committing to a response) — the actual
        guarantee against interleaved requests comes from _request_lock's
        real acquire in send_message/send_message_stream below, not this."""
        acquired = _request_lock.acquire(blocking=False)
        if acquired:
            _request_lock.release()
            return False
        return True

    def send_message(
        self,
        message: str,
        document_ids: list[str] | None = None,
        top_k: int | None = None,
    ) -> tuple[str, list, int]:
        self._ensure_documents_ready()

        if not _request_lock.acquire(blocking=False):
            raise ChatBusyError(
                "Still processing a previous message — please wait for it to finish."
            )
        try:
            history_snapshot = self._append_turn(ConversationTurn(role="user", content=message))

            try:
                answer, citations = rag_pipeline.answer_question(
                    question=message,
                    conversation_history=history_snapshot,
                    document_ids=document_ids,
                    top_k=top_k or settings.TOP_K,
                )
            except AppError:
                # Already a typed, user-facing error (e.g. missing API key) —
                # let it propagate as-is so main.py's handler returns the
                # right status code and message.
                self._pop_last_turn()  # don't keep a user turn with no answer
                raise
            except Exception as exc:  # noqa: BLE001 — genuinely unexpected failure
                logger.error(f"LLM call failed: {exc}")
                self._pop_last_turn()
                raise LLMProviderError(f"Failed to generate an answer: {exc}") from exc

            turns = len(
                self._append_turn(
                    ConversationTurn(role="assistant", content=answer, citations=citations)
                )
            )
            return answer, citations, turns
        finally:
            _request_lock.release()

    def send_message_stream(
        self,
        message: str,
        document_ids: list[str] | None = None,
        top_k: int | None = None,
    ):
        """Yields structured streaming events (see rag.pipeline.answer_question_stream)
        and persists the complete answer to history once the stream finishes."""
        self.validate_ready_for_chat()

        if not _request_lock.acquire(blocking=False):
            raise ChatBusyError(
                "Still processing a previous message — please wait for it to finish."
            )

        history_snapshot = self._append_turn(ConversationTurn(role="user", content=message))

        answer_parts: list[str] = []
        citations: list = []

        try:
            for event in rag_pipeline.answer_question_stream(
                question=message,
                conversation_history=history_snapshot,
                document_ids=document_ids,
                top_k=top_k or settings.TOP_K,
            ):
                if event["type"] == "token":
                    answer_parts.append(event["content"])
                elif event["type"] == "citations":
                    citations = event["citations"]
                yield event
        except Exception:
            # Mirror send_message's failure cleanup: a mid-stream error
            # (e.g. the LLM provider drops the connection) previously left
            # an orphaned user turn with no matching assistant response in
            # history (audit finding H1) — remove it so the next question's
            # prompt context isn't corrupted by a dangling, unanswered turn.
            self._pop_last_turn()
            raise
        else:
            self._append_turn(
                ConversationTurn(role="assistant", content="".join(answer_parts), citations=citations)
            )
        finally:
            _request_lock.release()


chat_service = ChatService()
