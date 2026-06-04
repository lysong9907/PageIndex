import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from server.services.chat_service import run_rag_pipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory chat history storage (per document)
_chat_histories: dict = {}


@router.post("/{document_id}/ask")
async def ask_question(document_id: str, request: Request):
    """Ask a question about a document. Returns SSE stream."""
    body = await request.json()
    question = body.get("question", "")
    if not question.strip():
        return {"error": "Question cannot be empty"}

    chat_history = body.get("chat_history", [])

    async def event_stream():
        full_answer = ""
        thinking = ""
        referenced_nodes = []

        async for event_type, data in run_rag_pipeline(document_id, question, chat_history):
            yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

            if event_type == "answer_chunk":
                full_answer += data.get("content", "")
            elif event_type == "thinking":
                thinking = data.get("content", "")
            elif event_type == "nodes_found":
                referenced_nodes = data.get("node_ids", [])

        # Save to history
        if document_id not in _chat_histories:
            _chat_histories[document_id] = []
        _chat_histories[document_id].append({"role": "user", "content": question})
        _chat_histories[document_id].append({
            "role": "assistant",
            "content": full_answer,
            "thinking": thinking,
            "referenced_nodes": referenced_nodes,
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/{document_id}/history")
async def get_chat_history(document_id: str):
    """Get chat history for a document session."""
    history = _chat_histories.get(document_id, [])
    return {"document_id": document_id, "messages": history}


@router.delete("/{document_id}/history")
async def clear_chat_history(document_id: str):
    """Clear chat history for a document."""
    _chat_histories.pop(document_id, None)
    return {"status": "cleared"}
