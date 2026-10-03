"""Routes for chat: ask questions, view history, and clear the conversation."""
import json

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ClearChatResponse,
    Citation,
)
from app.schemas.common import ErrorResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])

_error_responses = {
    400: {"model": ErrorResponse, "description": "No documents indexed yet"},
    429: {"model": ErrorResponse, "description": "Already processing a previous message"},
    502: {"model": ErrorResponse, "description": "LLM provider call failed"},
}


def _citation_to_schema(citation) -> Citation:
    return Citation(
        document_id=citation.document_id,
        filename=citation.filename,
        chunk_index=citation.chunk_index,
        snippet=citation.snippet,
        similarity_score=citation.similarity_score,
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("", response_model=ChatResponse, responses=_error_responses)
async def chat(payload: ChatRequest) -> ChatResponse:
    # chat_service.send_message does a blocking network call to the LLM
    # provider — offloaded to a thread so it doesn't stall the event loop
    # for every other concurrent request (audit finding C1). Note this is
    # NOT needed for /chat/stream below: Starlette's StreamingResponse
    # already runs sync generators via a threadpool internally
    # (see starlette.concurrency.iterate_in_threadpool), verified by
    # reading its source during this audit.
    answer, citations, turns = await run_in_threadpool(
        chat_service.send_message,
        message=payload.message,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )
    return ChatResponse(
        message=answer,
        citations=[_citation_to_schema(c) for c in citations],
        conversation_length=turns,
    )


@router.post("/stream", responses={400: _error_responses[400], 429: _error_responses[429]})
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    # Validated eagerly, *before* the stream opens: once StreamingResponse's
    # headers are sent the client has already committed to a 200 response,
    # so a typed 4xx error (e.g. "no documents indexed") has to happen here.
    chat_service.validate_ready_for_chat()

    def event_generator():
        try:
            for event in chat_service.send_message_stream(
                message=payload.message,
                document_ids=payload.document_ids,
                top_k=payload.top_k,
            ):
                if event["type"] == "token":
                    yield _sse_event("token", {"content": event["content"]})
                elif event["type"] == "citations":
                    citations = [_citation_to_schema(c).model_dump() for c in event["citations"]]
                    yield _sse_event("citations", {"citations": citations})
            yield _sse_event("done", {})
        except Exception as exc:  # noqa: BLE001 — stream already committed to 200; surface as an SSE error event
            yield _sse_event("error", {"message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering if deployed behind it
        },
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history() -> ChatHistoryResponse:
    history = chat_service.get_history()
    return ChatHistoryResponse(
        messages=[
            ChatMessage(
                role=turn.role,
                content=turn.content,
                citations=[_citation_to_schema(c) for c in turn.citations],
                timestamp=turn.timestamp,
            )
            for turn in history
        ]
    )


@router.delete("", response_model=ClearChatResponse)
async def clear_chat() -> ClearChatResponse:
    chat_service.clear_history()
    return ClearChatResponse()
