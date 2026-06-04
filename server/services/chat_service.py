import os
import json
import asyncio
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from server.services.tree_service import load_tree, get_skeleton, find_nodes_by_ids

TREE_SEARCH_PROMPT = """You are given a question and a tree structure of a document.
Each node contains a node id, node title, and a corresponding summary.
Your task is to find all nodes that are likely to contain the answer to the question.

Question: {question}

Document tree structure:
{tree_skeleton}

Please reply in the following JSON format:
{{
    "thinking": "<Your thinking process on which nodes are relevant to the question>",
    "node_list": ["node_id_1", "node_id_2"]
}}
Directly return the final JSON structure. Do not output anything else."""

ANSWER_PROMPT = """Based on the following document excerpts, answer the user's question.
Cite the relevant section titles in your answer.

Question: {question}

Document excerpts:
{context}

Provide a comprehensive answer in the same language as the question, based only on the provided excerpts."""


def _get_llm_config():
    """Read LLM config from environment, fallback to config.yaml."""
    cfg_path = Path(__file__).parent.parent.parent / "pageindex" / "config.yaml"
    yaml_cfg = {}
    if cfg_path.exists():
        import yaml
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            yaml_cfg = yaml.safe_load(f) or {}
    return {
        "api_key": os.getenv("CHATGPT_API_KEY", ""),
        "base_url": os.getenv("API_BASE_URL", yaml_cfg.get("api_base_url", None)),
        "model": os.getenv("LLM_MODEL", yaml_cfg.get("model", "qwen-plus")),
    }


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response text."""
    import re
    # Try to find JSON in code blocks first
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1).strip()
    # Try to find raw JSON
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"thinking": text, "node_list": []}


async def run_rag_pipeline(document_id: str, question: str, chat_history: list):
    """Async generator yielding (event_type, data) tuples for SSE."""
    cfg = _get_llm_config()
    client = AsyncOpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])

    # Load tree
    tree = load_tree(document_id)
    skeleton = get_skeleton(tree)

    # --- Phase 1: Tree Search ---
    yield ("phase", {"phase": "tree_search", "message": "Searching document tree..."})

    search_prompt = TREE_SEARCH_PROMPT.format(
        question=question,
        tree_skeleton=json.dumps(skeleton["structure"], ensure_ascii=False, indent=2)
    )

    try:
        search_response = await client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": search_prompt}],
            temperature=0,
        )
        search_text = search_response.choices[0].message.content
    except Exception as e:
        yield ("error", {"message": f"Tree search failed: {str(e)}"})
        return

    # Parse response
    parsed = _extract_json(search_text)
    thinking = parsed.get("thinking", "")
    node_ids = parsed.get("node_list", [])

    yield ("thinking", {"content": thinking})

    # Resolve node titles
    matched_nodes = find_nodes_by_ids(tree, node_ids)
    node_titles = [n.get("title", "Unknown") for n in matched_nodes]
    yield ("nodes_found", {
        "node_ids": node_ids,
        "node_titles": node_titles
    })

    if not matched_nodes:
        yield ("answer_chunk", {"content": "No relevant sections found in the document for this question."})
        yield ("done", {"referenced_nodes": [], "tokens_used": {}})
        return

    # --- Phase 2: Answer Generation with Streaming ---
    yield ("phase", {"phase": "generating_answer",
                      "message": f"Generating answer from {len(matched_nodes)} relevant sections..."})

    # Build context from matched nodes
    context_parts = []
    for node in matched_nodes:
        text = node.get("text", node.get("summary", ""))
        title = node.get("title", "Unknown")
        start = node.get("start_index", "?")
        end = node.get("end_index", "?")
        context_parts.append(f"[{title}] (pages {start}-{end}):\n{text}")
    context = "\n\n---\n\n".join(context_parts)

    answer_prompt = ANSWER_PROMPT.format(question=question, context=context)

    # Build message list with history
    messages = []
    for msg in chat_history[-6:]:  # Last 6 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": answer_prompt})

    try:
        stream = await client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield ("answer_chunk", {"content": delta.content})

    except Exception as e:
        yield ("error", {"message": f"Answer generation failed: {str(e)}"})
        return

    yield ("done", {
        "referenced_nodes": node_ids,
        "tokens_used": {}
    })
